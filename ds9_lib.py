#Library for handling DS9 scripting

import numpy as np #Import numpy
import ds9  #Import wrapper for allowing python script DS9 with XPA
import sys, os
from coordfuncs import *  #Import coordfuncs for handing spherical astronomy and coordinates
#Grab path to current working directory
current_working_directory = os.getcwd() + '/'

#global variables (for McD) [originally taken from observability.py options file]
mirror_field = False #Mirror field (needed for DCT)
observatory_latitude = 30.6714     #Latitude of observatory (deg. north), FOR MCDONALD OBSERVATORY 2.7M
observatory_longitude = 104.0225    #Longitude of observatory  (deg. west), FOR MCDONALD OBSERVATORY 2.7M
#img_size = 6.0     #Set 2MASS image size to NxN arcmin
band = 'k'      #Set 2MASS band ('h','j','k')
plate_scale = 0.119       #Slit View Camera plate-scale, arcsec per pixel, FOR MCDONALD OBSERVATORY 2.7M
gstar_mag_limit = 14.0        #Guide star search K-band mag. limit, the dimmest K-band mag. to search for guide stars
gstar_ra_limit_arcmin = 3.0     #Guide star search delta-RA limit (in arcmin) from  target, FOR MCDONALD OBSERVATORY 2.7M
gstar_dec_limit_arcmin = 3.0     #Guide star search delta-Dec. limit (in arcmin) from target, FOR MCDONALD OBSERVATORY 2.7M
n_gstars = 20      #Guide star search, star number limit (ie. 10 means find 10 brightest stars)



# gstar_dra_arcsec = 0.0  #Initialize these variables, if no guide star is used, just keep them zero
# gstar_ddec_arcsec = 0.0
# gstar_dra_deg = 0.0
# gstar_ddec_deg = 0.0
# gstar_sl = 0.0
# gstar_sw = 0.0


'''This function creates the region file for the IGRINS Slit View Camera (SVC) FOV
Rotation in Position Angle is accounted for via rotation matrix for the 
polygon used to represent the SVC FOV'''
def create_region_template(rotation, plate_scale, guidestar_dra=0, guidestar_ddec=0, guidestar_sl=0, guidestar_sw=0, mirror_field=False):
    zoom =  plate_scale / 0.119 #Set zoom scale to scale the FOV, the McDonald Observatory 2.7m plate scale is 0.119 so changing the plate scale in the options.inp file 
    default_slit_angle = 359.98672  #Default angle of the slit (East to west)
    x, y, poly_x, poly_y = loadtxt('scam-outline.txt', unpack=True) #Outline of SVC FOV, thanks to Henry Roe (private communication)
    poly_x = poly_x / 3600.0 #Convert arcseconds to degrees
    poly_y = poly_y / 3600.0
    if mirror_field: #If SCV field is mirrored (e.g. on DCT)...
        poly_y = -poly_y  #Mirror the polygon describing the FOV of the SCV
    # poly_x = [0.02714, 0.02712, 0.02593, 0.02462, 0.02412, 0.02422, 0.02429,  #Old polygon, now using new one from Henry Roe
    #           #Default x values for points in FOV polygon
    #           -0.00265, -0.02095, -0.02338, -0.02403, -0.02681, -0.02677, -0.02518,
    #           -0.02256, -0.01865, -0.01333, 0.0158, 0.0236]
    # poly_y = [-0.00825096, -0.00809768, -0.00462737, -0.00309165, 0.00030273, 0.00061059, 0.00618683,
    #           #Default y values for points in FOV polygon
    #           0.00582677, 0.00541191, 0.00319962, 0.00332299, -0.00340406, -0.00778661, -0.01318707,
    #           -0.01728969, -0.02215466, -0.02662075, -0.0258552, -0.01869832]
    rad_rot = radians(rotation)  #Convert degrees to radians for angle of rotation
    rotMatrix = array(
        [[cos(rad_rot), -sin(rad_rot)], [sin(rad_rot), cos(rad_rot)]])  #Set up rotation matrix for polygon
    [poly_x, poly_y] = rotMatrix.dot([poly_x, poly_y]) * zoom  #Apply rotation matrix to the FOV polygon, and scale it if necessary
    poly_xy = '('  #Make string to output for polygon points
    n = size(poly_x)  #Find number of points in polygon
    for i in range(n - 1):  #Loop through points 0 -> n-2
        poly_xy = poly_xy + str(poly_x[i]) + ', ' + str(poly_y[i]) + ', '
    poly_xy = poly_xy + str(poly_x[n - 1]) + ', ' + str(
        poly_y[n - 1]) + ')'  #Give final point the special format it needs
    total_slit_angle = longitude(default_slit_angle - rotation)  #Calculate angle to rotate slit box
    slit_angle = str(total_slit_angle.deg())  #Convert slit angle after applying rotation of IGRINS to a string
    output = []  #Set up array to output lines of text to region tmeplate file, as strings appended to the array
    output.append('# Region file format: DS9 version 4.1')  #Output top line to region file
    output.append(
        'global color=green dashlist=8 3 width=1 font="helvetica 10 normal roman" select=1 highlite=1 dash=0 fixed=0 edit=1 select=0 delete=1 include=1 source=1')  #Set up color, fonts, and stuff
    output.append('wcs0;fk5')  #Set coordinate system
    #compass_size = str(72.0 * zoom) #Scale compass size
    output.append(
        #'# compass(0,0,'+compass_size+'") compass=fk5 {N} {E} 1 1 font="helvetica 12 bold roman" color=blue fixed=0')  #Set compass (North and East arrows)
        '# compass(0,0) compass=fk5 {N} {E} 1 1 font="helvetica 12 bold roman" color=blue fixed=0 select=0')  #Set compass (North and East arrows)
    slit_length = str(15.0 * zoom) #Scale slit length
    slit_width = str(1.0 * zoom) #Scale slit width
    output.append('box(0,0,'+slit_length+'",'+slit_width+'",' + slit_angle + ') # color=green width=2 select=0')  #Display slit
    if abs(guidestar_dra) > 0. or abs(guidestar_ddec) > 0.:  #show guidestar if it exists
        output.append('point(' + str(guidestar_dra) + ',' + str(
            guidestar_ddec) + ') # point=circle font="helvetica 12 bold roman" color=yellow text={Offslit guide star [sl: ' + "%5.2f" % gstar_sl + ', sw:' + "%5.2f" % gstar_sw + ']} select=0')
    output.append('polygon' + poly_xy)  #Save SVC FOV polygon
    savetxt('IGRINS_svc_generated.tpl', output, fmt="%s")  #Save region template file for reading into ds9


'''This function creates the region file for the IGRINS Slit View Camera (SVC) FOV
Rotation in Position Angle is accounted for via rotation matrix for the 
polygon used to represent the SVC FOV'''
def create_region(coordobj, rotation, plate_scale, guidestar_dra=0, guidestar_ddec=0, guidestar_sl=0, guidestar_sw=0, mirror_field=False,
        show_scan=False, scan_blocks=None, scan_plus_90_deg=False):
    zoom =  plate_scale / 0.119 #Set zoom scale to scale the FOV, the McDonald Observatory 2.7m plate scale is 0.119 so changing the plate scale in the options.inp file 
    default_slit_angle = 359.98672  #Default angle of the slit (East to west)
    x, y, poly_x, poly_y = loadtxt('scam-outline.txt', unpack=True) #Outline of SVC FOV, thanks to Henry Roe (private communication)
    poly_x = poly_x / 3600.0 #Convert arcseconds to degrees
    poly_y = poly_y / 3600.0
    if mirror_field: #If SCV field is mirrored (e.g. on DCT)...
        poly_y = -poly_y  #Mirror the polygon describing the FOV of the SCV
    # poly_x = [0.02714, 0.02712, 0.02593, 0.02462, 0.02412, 0.02422, 0.02429,  #Old polygon, now using new one from Henry Roe
    #           #Default x values for points in FOV polygon
    #           -0.00265, -0.02095, -0.02338, -0.02403, -0.02681, -0.02677, -0.02518,
    #           -0.02256, -0.01865, -0.01333, 0.0158, 0.0236]
    # poly_y = [-0.00825096, -0.00809768, -0.00462737, -0.00309165, 0.00030273, 0.00061059, 0.00618683,
    #           #Default y values for points in FOV polygon
    #           0.00582677, 0.00541191, 0.00319962, 0.00332299, -0.00340406, -0.00778661, -0.01318707,
    #           -0.01728969, -0.02215466, -0.02662075, -0.0258552, -0.01869832]
    rad_rot = radians(rotation)  #Convert degrees to radians for angle of rotation
    rotMatrix = array(
        [[cos(rad_rot), -sin(rad_rot)], [sin(rad_rot), cos(rad_rot)]])  #Set up rotation matrix for polygon
    [poly_x, poly_y] = rotMatrix.dot([poly_x, poly_y]) * zoom  #Apply rotation matrix to the FOV polygon, and scale it if necessary
    poly_x /= cos(radians(coordobj.dec.deg()))
    poly_x += coordobj.ra.deg() #Add RA and Dec. position
    poly_y += coordobj.dec.deg()
    poly_xy = '('  #Make string to output for polygon points
    n = size(poly_x)  #Find number of points in polygon
    for i in range(n - 1):  #Loop through points 0 -> n-2
        poly_xy = poly_xy + str(poly_x[i]) + ', ' + str(poly_y[i]) + ', '
    poly_xy = poly_xy + str(poly_x[n - 1]) + ', ' + str(
        poly_y[n - 1]) + ')'  #Give final point the special format it needs
    total_slit_angle = longitude(default_slit_angle - rotation)  #Calculate angle to rotate slit box
    slit_angle = str(total_slit_angle.deg())  #Convert slit angle after applying rotation of IGRINS to a string
    output = []  #Set up array to output lines of text to region tmeplate file, as strings appended to the array
    output.append('# Region file format: DS9 version 4.1')  #Output top line to region file
    output.append(
        'global color=green dashlist=8 3 width=1 font="helvetica 10 normal roman" select=1 highlite=1 dash=0 fixed=0 edit=1 select=0 delete=1 include=1 source=1')  #Set up color, fonts, and stuff
    output.append('wcs0;fk5')  #Set coordinate system
    #compass_size = str(72.0 * zoom) #Scale compass size

    slit_length = str(15.0 * zoom) #Scale slit length
    slit_width = str(1.0 * zoom) #Scale slit width
    #Test plotting slitscan
    if show_scan:
        for block in scan_blocks:
            for i in range(len(block['sw'])):
                # # if not scan_plus_90_deg:
                # #     block_dra, block_ddec = convert_from_sl_sw_to_dra_ddec(block['sl']-guidestar_sl, block['sw'][i]-guidestar_sw, 270+rotation)
                # #     #output.append('box('+str(coordobj.ra.deg()-((block_dra/3600.0)/coordobj.dec.cos()))+','+str(coordobj.dec.deg()-(block_ddec/3600.0))+','+slit_length+'",'+slit_width+'",' + slit_angle + ') # color=#C0C0C0 width=1 select=0')  #Display slit
                # # else:
                # block_dra, block_ddec = convert_from_sl_sw_to_dra_ddec(block['sl']-guidestar_sl, block['sw'][i]-guidestar_sw, (90+rotation))
                block_dra, block_ddec = convert_from_sl_sw_to_dra_ddec(block['sl'], block['sw'][i], (90+rotation))
                block_dra = block_dra - guidestar_dra
                block_ddec = block_ddec - guidestar_ddec
                # output.append('box('+str(coordobj.ra.deg()-((block_dra/3600.0)/coordobj.dec.cos()))+','+str(coordobj.dec.deg()-(block_ddec/3600.0))+','+slit_length+'",'+slit_width+'",' + slit_angle + ') # color=#C0C0C0 width=1 select=0')  #Display slit

                #block_dra, block_ddec = convert_from_sl_sw_to_dra_ddec(block['sl']-guidestar_sl, block['sw'][i]-guidestar_sw, 90+rotation)
                output.append('box('+str(coordobj.ra.deg()-((block_dra/3600.0)/coordobj.dec.cos()))+','+str(coordobj.dec.deg()-(block_ddec/3600.0))+','+slit_length+'",'+slit_width+'",' + slit_angle + ') # color=#C0C0C0 width=1 select=0')  #Display slit

                



    compass_size = str(36.0 * zoom) #Scale compass size
    output.append(
        '# compass('+str(coordobj.ra.deg())+','+str(coordobj.dec.deg())+','+compass_size+'") compass=fk5 {N} {E} 1 1 font="helvetica 12 bold roman" color=blue fixed=0 select=0')  #Set compass (North and East arrows)

    output.append('box('+str(coordobj.ra.deg())+','+str(coordobj.dec.deg())+','+slit_length+'",'+slit_width+'",' + slit_angle + ') # color=green width=2 select=0')  #Display slit
    
    if abs(guidestar_dra) > 0. or abs(guidestar_ddec) > 0.:  #show guidestar if it exists
        output.append('point(' + str((guidestar_dra/3600.0/coordobj.dec.cos())+coordobj.ra.deg()) + ',' + str(
            guidestar_ddec/3600.0+coordobj.dec.deg()) + ') # point=circle font="helvetica 12 bold roman" color=yellow text={Offslit guide star [sl: ' + "%5.2f" % guidestar_sl + ', sw:' + "%5.2f" % guidestar_sw + ']} select=1')
    output.append('polygon' + poly_xy)  #Save SVC FOV polygon
    savetxt('IGRINS_svc_generated.reg', output, fmt="%s")  #Save region template file for reading into ds9



def make_finder_chart_in_ds9(target, guidestar, grab_image=True):

    #Set rotator variables
    delta_PA = 90.0 - float(target.PA.get())  #Default instrument East-west setting is 90 degrees in PA
    #breakpoint()
    ra = sex2deg(target.ra.get(), units='hms') #Convert to decimal degrees so we can easily add and subtract
    dec = sex2deg(target.dec.get(), units='dms')
    if target.use_proper_motion.get(): #Use target proper motion to set slit center 
        proper_motion_ra_distance_arcsec = float(target.proper_motion[0].get()) * 1e-3 * (float(target.epoch.get())-2000.0)
        proper_motion_dec_distance_arcsec = float(target.proper_motion[1].get()) * 1e-3 * (float(target.epoch.get())-2000.0)
        ra += proper_motion_ra_distance_arcsec / cos(radians(dec)) / 3600.0
        dec += proper_motion_dec_distance_arcsec / 3600.
    guidestar_dra = float(guidestar.dra.get()) #Defaults for guidestar
    guidestar_ddec =  float(guidestar.ddec.get())
    guidestar_sl =  float(guidestar.dG[0].get())
    guidestar_sw =  float(guidestar.dG[1].get())
    if target.use_slitscan.get(): #Adjust coordinates if using slitscan
        guidestar_sl, guidestar_sw = target.get_scan_sl_sw(int(target.scan_finder_row.get()), 
                                        int(target.scan_finder_col.get()),
                                        int(target.scan_finder_pos.get()))
        guidestar_slitscan_dra, guidestar_slitscan_ddec = convert_from_sl_sw_to_dra_ddec(guidestar_sl, guidestar_sw, float(target.PA.get()))
        if not target.scan_rotation.get()=='+90 deg PA':
            ra += (guidestar_dra-guidestar_slitscan_dra) / cos(radians(dec)) / 3600.0
            dec += (guidestar_ddec-guidestar_slitscan_ddec) / 3600.   
            guidestar_dra =  guidestar_slitscan_dra
            guidestar_ddec = guidestar_slitscan_ddec 
        else:
            ra += (guidestar_dra+guidestar_slitscan_dra) / cos(radians(dec)) / 3600.0
            dec += (guidestar_ddec+guidestar_slitscan_ddec) / 3600.       
            guidestar_dra =  -guidestar_slitscan_dra
            guidestar_ddec = -guidestar_slitscan_ddec       

    obj_coords = coords(ra, dec)
    print(ra, dec)
    # else:
    #     ra = target.ra.get()
    #     dec = target.dec.get()
    #     print(ra+' '+dec)
    #     obj_coords = coord_query(ra+' '+dec) #Put RA and DEC in a coords object
    #ds9.open()  #Open DS9
    #ds9.wait(2.0) #Used to be needed, commented out for now because I think I fixed this bug and can now speed things up
    if grab_image==True:
        ds9.set('single')  #set single display mode
        if target.survey.get() == '2MASS K-band': #Use HEASARC Sky View server to get mosaicced 2MASS images, to get rid of bug from where images got sliced from the 2MASS server
            ds9.set('skyview open')
            ds9.set('skyview pixels 900 900') #Set resoultion of image retrieved
            #n_pixels = str(int(np.round(900 * (fov/6)))) #Calculate number of pixels to use for resolution of 2MASS image, normalized to 900 pixels for 6 arcmin on a side
            #ds9.set('skyview pixels '+n_pixels+' '+n_pixels) #Set resoultion of image retrieved
            #ds9.set('skyview size '+ str(img_size) + ' ' + str(img_size) + ' arcmin')#Set size of image
            ds9.set('skyview size '+ target.fov.get() + ' ' + target.fov.get() + ' arcmin')#Set size of image
            ds9.set('skyview survey 2MASS-'+band) #Use HEASARC Sky View server to get mosaicced 2MASS images
            # if obj_choice == '2':  #If user specifies object name
            #    ds9.set('skyview name ' + obj_input.replace(" ", "_"))  #Retrieve 2MASS image
            # else:  #If user specifies object coordiantes
            #    ds9.set('skyview coord ' + str(obj_coords.ra.deg()) + ' ' + str(
            #        obj_coords.dec.deg()) + ' degrees')  #Retrieve 2MASS image
            ds9.set('skyview coord ' + str(obj_coords.ra.deg()) + ' ' + str(
               obj_coords.dec.deg()) + ' degrees')  #Retrieve 2MASS image
            ds9.set('skyview close') #Close skyserver window
        elif target.survey.get() == 'POSS2 IR': #Use STSCI DSS server to grab the POSS2 Infrared survey
            ds9.set('dssstsci open')
            ds9.set('dssstsci size '+ target.fov.get() + ' ' + target.fov.get() + ' arcmin')#Set size of image
            ds9.set('dssstsci survey poss2ukstu_ir') #Set survey + band
            ds9.set('dssstsci '+ str(obj_coords.ra.deg()) + ' ' + str(
               obj_coords.dec.deg()) + ' degrees')  #Retrieve  image
            #ds9.set('dssstsci close') #Close window when done
        #Old 2MASS server commented out for now, probably obselete, using HEASARC Sky View server now
        #HEASARC Sky Viewer server does not appear to be working anymore in DS9 so falling back on the old 2MASS image server, it's not ideal but it should work (mostly)
        # ds9.set('2mass close')  #Close 2MASS window
        # ds9.set('2mass survey ' + band)  #Load 2MASS survey
        # ds9.set('2mass size ' + str(img_size) + ' ' + str(
        #    img_size) + ' arcmin')  #Set size of image (weird issues here, only strips extracted)
        # if obj_choice == '2':  #If user specifies object name
        #    ds9.set('2mass name ' + obj_input.replace(" ", "_"))  #Retrieve 2MASS image
        # else:  #If user specifies object coordiantes
        #    ds9.set('2mass coord ' + str(obj_coords.ra.deg()) + ' ' + str(
        #        obj_coords.dec.deg()) + ' degrees')  #Retrieve 2MASS image
        # ds9.set('2mass close')  #Close 2MASS window

        ds9.set('scale log')  #Set view to log scale
        ds9.set('scale Zmax')  #Set scale limits to Zmax, looks okay
    # else:  #If user does specify their own fits file, use it
    #     ds9.set('fits ' + finder_chart_fits)  #Load fits fits file

    # #Grab guide star RA and Dec. from user input if specified
    # if gstar_choice == '1':  #Grab guide star coordinates from dRA & dDec input in arcseconds (distance guide star is from target in arcseconds)
    #dra, ddec = gstar_input.split(' ')  #Sepearte delta RA and Dec. by a space entered by the user
    # dra = float(dra) / 3600.0  #Convert arcseconds to degrees
    # ddec = float(ddec) / 3600.0  #convert arcseconds to degrees
    # gstar_coords = coords(obj_coords.ra.deg() + dra / obj_coords.dec.cos(), obj_coords.dec.deg() + ddec)
    # elif gstar_choice == '2':  #Grab guide star coordinates from RA & Dec input
    #     gstar_coords = coord_query(gstar_input)
    # elif gstar_choice == '3':  #Grab guide star coordinates from name lookup on internet
    #     gstar_coords = name_query(gstar_input)

    # if gstar_choice != '0' and gstar_choice != '4':  #If single guide star actually put in by user calculate the following parameters...
    #     gstar_dra_arcsec = ra_seperation(obj_coords, gstar_coords,
    #                                      units='arcsec')  #position of guide star from object in arcseconds
    #     gstar_ddec_arcsec = dec_seperation(obj_coords, gstar_coords,
    #                                        units='arcsec')  #position of guide star from object in arcseconds
    #     gstar_dra_deg = gstar_dra_arcsec / 3600.0  #position of guide star from object in degrees
    #     gstar_ddec_deg = gstar_ddec_arcsec / 3600.0  #position of guide star from object in degrees
    #     gstar_dx = (-gstar_dra_arcsec * cos(radians(PA - 45.0)) + gstar_ddec_arcsec * sin(
    #         radians(PA - 45.0)) ) / plate_scale  #guide star position in pixels in the SVC display
    #     gstar_dy = (gstar_dra_arcsec * sin(radians(PA - 45.0)) + gstar_ddec_arcsec * cos(
    #         radians(PA - 45.0)) ) / plate_scale  #guide star position in pixels in the SVC display
    #     gstar_sl = -gstar_dra_arcsec * cos(radians(PA - 90.0)) + gstar_ddec_arcsec * sin(
    #         radians(PA - 90.0))  #guide star position relative to slit in arcseconds
    #     gstar_sw = gstar_dra_arcsec * sin(radians(PA - 90.0)) + gstar_ddec_arcsec * cos(
    #         radians(PA - 90.0))  #guide star position relative to slit in arcseconds

    # create_region_template(delta_PA, plate_scale, gstar_dra_deg, gstar_ddec_deg, gstar_sl,
    #                        gstar_sw, mirror_field)  #Make region template file rotated and the specified PA
    # create_region(obj_coords, delta_PA, plate_scale, gstar_dra_deg, gstar_ddec_deg, gstar_sl,
    #                        gstar_sw, mirror_field)  #Make region template file rotated and the specified PA
    ds9.set('regions delete all')
    create_region(obj_coords, delta_PA, plate_scale, guidestar_dra=guidestar_dra, guidestar_ddec=guidestar_ddec, guidestar_sl=guidestar_sl, guidestar_sw=guidestar_sw, mirror_field=mirror_field, 
        show_scan=target.use_slitscan.get(), scan_blocks=target.scan_blocks, scan_plus_90_deg=target.scan_rotation.get()=='+90 deg PA')  #Make region template file rotated and the specified PA
    #ds9.set(
    #    'regions template IGRINS_svc_generated.tpl at ' + obj_coords.showcoords() + ' fk5')  #Read in regions template file
    #ds9.set('pan to '+obj_coords.showcoords() + ' wcs fk5')
    #ds9.set('regions template ' + current_working_directory + 'IGRINS_svc_generated.tpl at,  ' + obj_coords.showcoords() + ' wcs fk5')
    #ds9.set('regions template ' + current_working_directory + 'IGRINS_svc_generated.tpl')
    ds9.set('regions ' + current_working_directory + 'IGRINS_svc_generated.reg')
    ds9.set('regions select all')
    ds9.set('regions move back')
    ds9.set('regions group FOV new')
    ds9.set('regions select none')  #Deslect regions when finished
    ds9.set(
        'align yes')  #Set north to be up and east to be left, before rotating, for weird fits files that open at odd angles
    ds9.rotto(-45 + delta_PA)  #Set orientation to match IGRINS guider

    ds9.set('pan to ' + obj_coords.showcoords() + ' wcs fk5')  #Center frame on target object
    ds9.set('zoom to fit')
    ds9.set('zoom 1.8')  #Try to set the zoom to easily see the IGRINS FOV
    ds9.set('mode pointer')  #Go to this standard editing mode in DS9

    # if gstar_choice == '4':  #If user specifies code to find guide stars automatically
    #     gstar_dec_limit = gstar_dec_limit / (2.0 * 60.0)  #Convert limit in Dec. to degrees
    #     gstar_ra_limit = gstar_ra_limit / (2.0 * 60.0 * obj_coords.dec.cos())  #Convert limit in RA to degrees
    #     ds9.set('catalog 2mass')  #Initialize catalog
    #     # ds9.set("catalog filter '$RAJ2000>=" + str(obj_coords.ra.deg() - gstar_ra_limit) + "&&$RAJ2000<=" + str(
    #     #     obj_coords.ra.deg() + gstar_ra_limit) \
    #     #         + "&&$DEJ2000>=" + str(obj_coords.dec.deg() - gstar_dec_limit) + "&&$DEJ2000<=" + str(
    #     #     obj_coords.dec.deg() + gstar_dec_limit) \
    #     #         + "&&$Kmag<=" + str(gstar_mag_limit) + "'")  #Load catalog
    #     ds9.set(r"catalog filter '$RAJ2000>=" + str(obj_coords.ra.deg() - gstar_ra_limit) + r" $RAJ2000<=" + str(
    #         obj_coords.ra.deg() + gstar_ra_limit) \
    #             + r" $DEJ2000>=" + str(obj_coords.dec.deg() - gstar_dec_limit) + r" $DEJ2000<=" + str(
    #         obj_coords.dec.deg() + gstar_dec_limit) \
    #             + r" $Kmag<=" + str(gstar_mag_limit) + r"'")  #Load catalog
    #     ds9.set(
    #         "catalog sort 'Kmag' incr")  #Sort list by starting from brightest K-band mag. and getting dimmer as you go down
    #     ds9.set("catalog export tsv " + current_working_directory + "tmp.dat")  #Save catalog list as a tab seperated value file for later trimming
    #     lines = open('tmp.dat').readlines()  #Open catalog list tsv file into memory
    #     if len(lines) > 1:
    #         open('tmp.dat', 'w').writelines(
    #             lines[0:n_gstars + 1])  #Truncate by maximum number of guide stars and save catalog list
    #         ds9.set('catalog clear')  #Clear 2MASS catalog
    #         ds9.set('catalog close')  #Close 2MASS catalog window
    #         ds9.set('catalog import tsv ' + current_working_directory + 'tmp.dat')  #Load only brightest stars to be potential guide stars
    #         ds9.set(
    #             'mode catalog')  #Set mode to catalog so user can click on possible guide stars and look at their stats
    #         gra, gdec, gmag = loadtxt('tmp.dat', usecols=(0, 1, 9), delimiter='\t', unpack=True,
    #                                   skiprows=1)  #Grab RA, Dec., and K-mag from catalog
    #         gra = ascontiguousarray(gra) #Fix a bug
    #         gdec = ascontiguousarray(gdec)
    #         gmag = ascontiguousarray(gmag)
    #         n_gstars = size(gra)  #reset n_gstars to the actual number of guide stars found
    #         command_line_output.append('Guide stars found:')  #Output for command line
    #         command_line_output.append('K-mag:\t sl: \t sw: \t\t Coordinates (J2000):')  #Output for command line
    #         for i in range(n_gstars):  #Loop through each guide star found and
                
    #             gstar_coords = coords(gra[i], gdec[i])
    #             found_gstar_dra_arcsec = ra_seperation(obj_coords, gstar_coords,
    #                                                    units='arcsec')  #position of guide star from object in arcseconds
    #             found_gstar_ddec_arcsec = dec_seperation(obj_coords, gstar_coords,
    #                                                      units='arcsec')  #position of guide star from object in arcseconds
    #             gstar_dx = (-found_gstar_dra_arcsec * cos(radians(PA - 45.0)) + found_gstar_ddec_arcsec * sin(
    #                 radians(PA - 45.0)) ) / plate_scale  #guide star position in pixels in the SVC display
    #             gstar_dy = (found_gstar_dra_arcsec * sin(radians(PA - 45.0)) + found_gstar_ddec_arcsec * cos(
    #                 radians(PA - 45.0)) ) / plate_scale  #guide star position in pixels in the SVC display
    #             gstar_sl = -found_gstar_dra_arcsec * cos(radians(PA - 90.0)) + found_gstar_ddec_arcsec * sin(
    #                 radians(PA - 90.0))  #guide star position relative to slit in arcseconds
    #             gstar_sw = found_gstar_dra_arcsec * sin(radians(PA - 90.0)) + found_gstar_ddec_arcsec * cos(
    #                 radians(PA - 90.0))  #guide star position relative to slit in arcseconds
    #             command_line_output.append("%7.2f" % gmag[
    #                 i] + '\t' + "%7.2f" % gstar_sl + '\t' + "%7.2f" % gstar_sw + '\t\t' + gstar_coords.showcoords())  #Save info on found guide stars to the command line
    #             ds9.draw('fk5; point(' + str(gra[i]) + ',' + str(
    #                 gdec[i]) + ') # point=cross font={helvetica 9 bold roman} color=yellow text={[K: ' \
    #                      + str(gmag[
    #                 i]) + '; SL: ' + "%5.2f" % gstar_sl + '; SW: ' + "%5.2f" % gstar_sw + ']}')  #Put pointer regions to guide stars in DS9
    #     else:
    #         ds9.set('catalog clear')  #Clear 2MASS catalog
    #         ds9.set('catalog close')  #Close 2MASS catalog window
    #         print('ERROR: No possible guide stars found. Check target position and then the mangitude, RA, & Dec limits in options.inp and retry.')    


#Search for guide stars
def search_for_guide_stars(target_ra, target_dec, n_gstars, PA, survey, use_proper_motion, epoch):
    obj_coords = coord_query(target_ra+' '+target_dec) #Put RA and DEC in a coords object
    gstar_dec_limit = gstar_dec_limit_arcmin / (2.0 * 60.0)  #Convert limit in Dec. to degrees
    gstar_ra_limit = gstar_ra_limit_arcmin / (2.0 * 60.0 * obj_coords.dec.cos())  #Convert limit in RA to degrees
    if survey == 'Gaia DR2':
        ds9.set('catalog gaia')
        ds9.set(r"catalog filter $_RAJ2000>=" + str(obj_coords.ra.deg() - gstar_ra_limit) + r"&&$_RAJ2000<=" + str(
            obj_coords.ra.deg() + gstar_ra_limit) \
                + r"&&$_DEJ2000>=" + str(obj_coords.dec.deg() - gstar_dec_limit) + r"&&$_DEJ2000<=" + str(
            obj_coords.dec.deg() + gstar_dec_limit) \
                + r"&&$RPmag<=" + str(gstar_mag_limit+3.0) + r"&&$RPmag>0.01")  #Load catalog
    #    elif survey == '2MASS point source':
    ds9.set('catalog 2mass')  #Initialize catalog
    # ds9.set("catalog filter '$RAJ2000>=" + str(obj_coords.ra.deg() - gstar_ra_limit) + "&&$RAJ2000<=" + str(
    #     obj_coords.ra.deg() + gstar_ra_limit) \
    #         + "&&$DEJ2000>=" + str(obj_coords.dec.deg() - gstar_dec_limit) + "&&$DEJ2000<=" + str(
    #     obj_coords.dec.deg() + gstar_dec_limit) \
    #         + "&&$Kmag<=" + str(gstar_mag_limit) + "'")  #Load catalog
    ds9.set(r"catalog filter $RAJ2000>=" + str(obj_coords.ra.deg() - gstar_ra_limit) + r"&&$RAJ2000<=" + str(
        obj_coords.ra.deg() + gstar_ra_limit) \
            + r"&&$DEJ2000>=" + str(obj_coords.dec.deg() - gstar_dec_limit) + r"&&$DEJ2000<=" + str(
        obj_coords.dec.deg() + gstar_dec_limit) \
            + r"&&$Kmag<=" + str(gstar_mag_limit))  #Load catalog


    if survey == 'Gaia DR2':
        ds9.set('catalog match error 5 arcsec')
        ds9.set('catalog match')
    #ds9.set("catalog sort '2_Kmag' incr")  #Sort list by starting from brightest K-band mag. and getting dimmer as you go down
    ds9.set("catalog sort 'Kmag' incr")  #Sort list by starting from brightest K-band mag. and getting dimmer as you go down
    ds9.set("catalog export tsv " + current_working_directory + "tmp.dat")  #Save catalog list as a tab seperated value file for later trimming
    lines = open('tmp.dat').readlines()  #Open catalog list tsv file into memory
    #breakpoint()
    if len(lines) > 1:
        open('tmp.dat', 'w').writelines(
            lines[0:n_gstars + 1])  #Truncate by maximum number of guide stars and save catalog list
        ds9.set('catalog clear')  #Clear 2MASS catalo, note run 3 times to close all the catalog windows
        ds9.set('catalog close')  #Close 2MASS catalog window
        if survey == 'Gaia DR2': #If using Gaia
            ds9.set('catalog clear')  #Clear 2MASS catalog
            ds9.set('catalog close')  #Close 2MASS catalog window
            ds9.set('catalog clear')  #Clear 2MASS catalog
            ds9.set('catalog close')  #Close 2MASS catalog window
            gra, gdec, gmag, gpra, gpdec = genfromtxt('tmp.dat', usecols=(0, 1, 43, 9, 11), delimiter='\t', unpack=True,
                                     skip_header=1, missing_values='', filling_values=0)  #Grab RA, Dec., K-mag and proper motion from catalog
            gpra = ascontiguousarray(gpra)
            gpdec = ascontiguousarray(gpdec)
        else: #If just using 2MASS gdec source catalog
            gra, gdec, gmag = loadtxt('tmp.dat', usecols=(0, 1, 9), delimiter='\t', unpack=True,
                                     skiprows=1)  #Grab RA, Dec., and K-mag from catalog
        gra = ascontiguousarray(gra) #Fix a bug
        gdec = ascontiguousarray(gdec)
        gmag = ascontiguousarray(gmag)
        n_gstars = size(gra)  #reset n_gstars to the actual number of guide stars found
        print('Guide stars found:')  #Output for command line
        print('K-mag:\t sl: \t sw: \t\t Coordinates (J2000):')  #Output for command line
        for i in range(n_gstars):  #Loop through each guide star found and
            
            gstar_coords = coords(gra[i], gdec[i])
            found_gstar_dra_arcsec = ra_seperation(obj_coords, gstar_coords,
                                                   units='arcsec')  #position of guide star from object in arcseconds
            found_gstar_ddec_arcsec = dec_seperation(obj_coords, gstar_coords,
                                                     units='arcsec')  #position of guide star from object in arcseconds
            if use_proper_motion == True and survey == 'Gaia DR2': #If using the Gaia catalog and user specifies they want to use proper motion, apply proper motion here
                proper_motion_ra_distance_arcsec = gpra[i] * 1e-3 * (epoch-2000.0)
                proper_motion_dec_distance_arcsec = gpdec[i] * 1e-3 * (epoch-2000.0)
                found_gstar_dra_arcsec += proper_motion_ra_distance_arcsec
                found_gstar_ddec_arcsec += proper_motion_dec_distance_arcsec
                gra += proper_motion_ra_distance_arcsec / cos(radians(gdec)) / 3600.0
                gdec += proper_motion_dec_distance_arcsec / 3600.0
            # gstar_dx = (-found_gstar_dra_arcsec * cos(radians(PA - 45.0)) + found_gstar_ddec_arcsec * sin(
            #     radians(PA - 45.0)) ) / plate_scale  #guide star position in pixels in the SVC display
            # gstar_dy = (found_gstar_dra_arcsec * sin(radians(PA - 45.0)) + found_gstar_ddec_arcsec * cos(
            #     radians(PA - 45.0)) ) / plate_scale  #guide star position in pixels in the SVC display
            gstar_sl = -found_gstar_dra_arcsec * cos(radians(PA - 90.0)) + found_gstar_ddec_arcsec * sin(
                radians(PA - 90.0))  #guide star position relative to slit in arcseconds
            gstar_sw = found_gstar_dra_arcsec * sin(radians(PA - 90.0)) + found_gstar_ddec_arcsec * cos(
                radians(PA - 90.0))  #guide star position relative to slit in arcseconds
            print("%7.2f" % gmag[
                i] + '\t' + "%7.2f" % gstar_sl + '\t' + "%7.2f" % gstar_sw + '\t\t' + gstar_coords.showcoords())  #Save info on found guide stars to the command line
            ds9.draw('fk5 ; point(' + str(gra[i]) + ',' + str(
                gdec[i]) + ') # point=cross font={helvetica 9 bold roman} color=yellow text={[K: ' \
                     + str(gmag[
                i]) + '; SL: ' + "%5.2f" % gstar_sl + '; SW: ' + "%5.2f" % gstar_sw + r']} tag={guidestars} move=0')  #Put pointer regions to guide stars in DS9
        ds9.set('regions group guidestars movefront') #Move guidestar regions to front
        ds9.set('mode region') #Set catalog mode so user can select the star they want
    else:
        ds9.set('catalog clear')  #Clear 2MASS catalog
        ds9.set('catalog close')  #Close 2MASS catalog window
        print('ERROR: No possible guide stars found. Check target position and then the mangitude, RA, & Dec limits in options.inp and retry.')    



#Convert dRA and dDec provided by user for guide star to dG SL SW based on slit PA
def convert_from_dra_ddec_to_sl_sw(dra_arcsec, ddec_arcsec, PA):
        sl = -dra_arcsec * cos(radians(PA - 90.0)) + ddec_arcsec * sin(
            radians(PA - 90.0))  #guide star position relative to slit in arcseconds
        sw = dra_arcsec * sin(radians(PA - 90.0)) + ddec_arcsec * cos(
            radians(PA - 90.0))  #guide star position relative to slit in arcseconds
        return sl, sw


def convert_from_sl_sw_to_dra_ddec(sl, sw, PA):
        dra_arcsec = -sl * cos(radians(-PA + 90.0)) + sw * sin(
            radians(-PA + 90.0))  #guide star position relative to slit in arcseconds
        ddec_arcsec = sl * sin(radians(-PA + 90.0)) + sw * cos(
            radians(-PA + 90.0))  #guide star position relative to slit in arcseconds
        return dra_arcsec, ddec_arcsec



def convert_guide_star_from_ra_dec_to_dra_ddec(gstar_ra, gstar_dec, target_ra, target_dec):
        gstar_coords = coord_query(gstar_ra+' '+gstar_dec) #Put RA and DEC in a coords object
        target_coords = coord_query(target_ra+' '+target_dec) #Put RA and DEC in a coords object
        gstar_dra_arcsec = ra_seperation(target_coords, gstar_coords,
                                         units='arcsec')  #position of guide star from object in arcseconds
        gstar_ddec_arcsec = dec_seperation(target_coords, gstar_coords,
                                           units='arcsec')  #position of guide star from object in arcseconds
        return gstar_dra_arcsec, gstar_ddec_arcsec


#Grab guide star from selected region
def grab_guide_star():
    result = ds9.get('regions -format ds9 -system wcs -sky fk5 -skyformat sexagesimal -strip yes selected')
    return result

