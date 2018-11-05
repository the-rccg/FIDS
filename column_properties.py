# Column properties

column_properties = {
    # Data Parameters
    'RA': {
        'desc':'right ascention from photometry catalog',
        'primary':True},
    'DEC': {
        'desc':'declination from photometry catalog',
        'primary':True},
    'field': {
        'desc':'field in the brick',
        'primary':False},
    'inside_brick': {
        'desc':'inside the brick boundaries',
        'primary':False},
    'inside_chigap': {
        'desc':'in ACS chip gap',
        'primary':False},
    # Photometry (units are *flux* [not mag])
    #   (units are normalized Vega fluxes, e.g., flux/flux_vega)
    'HST_WFC3_F275W': {
        'desc':'HST_WFC3_F275W',
        'primary':True},
    'HST_ACS_WFC3_F475W': {
        'desc':'HST_ACS_WFC3_F475W',
        'primary':True},
    'HST_ACS_WFC3_F814W': {
        'desc':'HST_ACS_WFC3_F814W',
        'primary':True},
    'HST_WFC3_F110W': {
        'desc':'HST_WFC3_F110W',
        'primary':True},
    'HST_WFC3_F160W': {
        'desc':'HST_WFC3_F160W',
        'primary':True},
    # BEAST goodness-of-fit metrics
    'Pmax': {
        'desc':'maxium probability of nD PDF',
        'primary':False},
    'chi2min': {
        'desc':'minimum value of chisqr',
        'primary':False},
    # BEAST Fitting parameters
    # The results come in three flavors
    # X_Best = best fit value
    # ["traditional" values]
    # X_Exp = expectation value (average weighted by 1D PDF)
    # [best when not using uncertainties]
    # X_p50 = 50% value from 1D PDF
    # X_p16 = 16% value from 1D PDF (minus 1 sigma)
    # X_p84 = 84% value from 1D PDF (plus 1 sigma)
    # [best when using uncertainites]
    # [use p50 - (p50-p16) + (p84 - p50) when quoting results with uncertainties]

    # Dust Parameters 
    'Av': {
        'desc':'A(V) = visual extinction in magnitudes',
        'primary':True},
    'Rv': {
        'desc':'R(V) = A(V)/E(B-V) = ratio of total to selective extinction',
        'primary':True},
    'f_A': {
        'desc':'fraction in extinction curve from A component (MW)',
        'primary':True},
    'Rv_A': {
        'desc':'R(V)_A = R(V) of A component of BEAST R(V)-f_A model of extinction curves',
        'primary':False},
    # Stellar Parameters
    'M_ini': {
        'desc':'initial stellar mass in solar masses',
        'primary':True},
    'logA': {
        'desc':'log10 of the stellar age (in years)',
        'primary':True},
    'Z': {
        'desc':'stellar metallicity [discrete]',
        'primary':True},
    'M_act': {
        'desc':'current stellar mass in solar masses',
        'primary':False},
    'logL': {
        'desc':'log10 of the stellar luminosity',
        'primary':False},
    'logT': {
        'desc':'log10 of the stellar effective temperature',
        'primary':False},
    'logg': {
        'desc':'log10 of the stellar surface gravity',
        'primary':False},
    'mbol': {
        'desc':'bolometric magnitude(????)',
        'primary':False},
    'radius': {
        'desc':'stellar radius',
        'primary':False},
    # BEAST Model predicted values
}
#
## ----------------------------
## 
## [same flavors as the BEAST fit parameters]
## 
## HST: Hubble Space Telescope
## logHST_WFC3_F275W_nd = log10 of the unextinguished WFC3 F275W flux
## logHST_WFC3_F275W_wd = log10 of the extinguished WFC3 F275W flux
## logHST_WFC3_F336W_nd = log10 of the unextinguished WFC3 F336W flux
## logHST_WFC3_F336W_wd = log10 of the extinguished WFC3 F336W flux
## logHST_ACS_WFC_F475W_nd = log10 of the unextinguished ACS F475W flux
## logHST_ACS_WFC_F475W_wd = log10 of the extinguished ACS F475W flux
## logHST_ACS_WFC_F814W_nd = log10 of the unextinguished ACS F814W flux
## logHST_ACS_WFC_F814W_wd = log10 of the extinguished ACS F814W flux
## logHST_WFC3_F110W_nd = log10 of the unextinguished WFC3 F110W flux
## logHST_WFC3_F110W_wd = log10 of the extinguished WFC3 F110W flux
## logHST_WFC3_F160W_nd = log10 of the unextinguished WFC3 F160W flux
## logHST_WFC3_F160W_wd = log10 of the extinguished WFC3 F160W flux
## 
## GALEX: GALexy Evolution eXplorer (only UV)
## logGALEX_FUV_nd = log10 of the unextinguished GALEX FUV flux
## logGALEX_FUV_wd = log10 of the extinguished GALEX FUV flux
## logGALEX_NUV_nd = log10 of the unextinguished GALEX FUV flux
## logGALEX_NUV_wd = log10 of the extinguished GALEX FUV flux
## 
## logF_UV_6_13e_nd = log10 of the unextinguished flux between 6 and 13 eV
## logF_UV_6_13e_wd = log10 of the extinguished flux between 6 and 13 eV
## 
## logF_QION_nd = log10 of the unextinguished ionizing flux (***do not use for PHAT results - incorrect***)
## logF_QION_wd = log10 of the extinguished ionizing flux (***do not use for PHAT results - incorrect***)
## 
## Extras
## ------
## 
## specgrid_indx = index of model in the spectral grid
## Pmax_indx = index in BEAST grid of Pmax
## chi2min_indx = index in BEAST grid of chi2min

