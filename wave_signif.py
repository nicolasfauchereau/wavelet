def wave_signif(Y,dt,scale1,sigtest=-1,lag1=-1,siglvl=-1,dof=-1,mother=-1,param=-1):
    """
    This function is the translation of wave_signif.m by Torrence and Compo
    use scipy function "chi2" instead of  chisquare_inv

    The following is the original comment in wave_signif.m

    %WAVE_SIGNIF  Significance testing for the 1D Wavelet transform WAVELET
    %
    %   [SIGNIF,FFT_THEOR] = ...
    %      wave_signif(Y,DT,SCALE,SIGTEST,LAG1,SIGLVL,DOF,MOTHER,PARAM)
    %
    % INPUTS:
    %
    %    Y = the time series, or, the VARIANCE of the time series.
    %        (If this is a single number, it is assumed to be the variance...)
    %    DT = amount of time between each Y value, i.e. the sampling time.
    %    SCALE = the vector of scale indices, from previous call to WAVELET.
    %
    %
    % OUTPUTS:
    %
    %    SIGNIF = significance levels as a function of SCALE
    %    FFT_THEOR = output theoretical red-noise spectrum as fn of PERIOD
    %
    %
    % OPTIONAL INPUTS:
    % *** Note *** setting any of the following to -1 will cause the default
    %               value to be used.
    %
    %    SIGTEST = 0, 1, or 2.    If omitted, then assume 0.
    %
    %         If 0 (the default), then just do a regular chi-square test,
    %             i.e. Eqn (18) from Torrence & Compo.
    %         If 1, then do a "time-average" test, i.e. Eqn (23).
    %             In this case, DOF should be set to NA, the number
    %             of local wavelet spectra that were averaged together.
    %             For the Global Wavelet Spectrum, this would be NA=N,
    %             where N is the number of points in your time series.
    %         If 2, then do a "scale-average" test, i.e. Eqns (25)-(28).
    %             In this case, DOF should be set to a
    %             two-element vector [S1,S2], which gives the scale
    %             range that was averaged together.
    %             e.g. if one scale-averaged scales between 2 and 8,
    %             then DOF=[2,8].
    %
    %    LAG1 = LAG 1 Autocorrelation, used for SIGNIF levels. Default is 0.0
    %
    %    SIGLVL = significance level to use. Default is 0.95
    %
    %    DOF = degrees-of-freedom for signif test.
    %         IF SIGTEST=0, then (automatically) DOF = 2 (or 1 for MOTHER='DOG')
    %         IF SIGTEST=1, then DOF = NA, the number of times averaged together.
    %         IF SIGTEST=2, then DOF = [S1,S2], the range of scales averaged.
    %
    %       Note: IF SIGTEST=1, then DOF can be a vector (same length as SCALEs),
    %            in which case NA is assumed to vary with SCALE.
    %            This allows one to average different numbers of times
    %            together at different scales, or to take into account
    %            things like the Cone of Influence.
    %            See discussion following Eqn (23) in Torrence & Compo.
    %
    %
    %----------------------------------------------------------------------------
    %   Copyright (C) 1995-1998, Christopher Torrence and Gilbert P. Compo
    %   University of Colorado, Program in Atmospheric and Oceanic Sciences.
    %   This software may be used, copied, or redistributed as long as it is not
    %   sold and this copyright notice is reproduced on each copy made.  This
    %   routine is provided as is without any express or implied warranties
    %   whatsoever.
    %----------------------------------------------------------------------------
    """
    from scipy.stats import chi2
    import numpy as np

    try:
        n1=len(Y)
    except:
        n1=1
    J1 = len(scale1) - 1
    scale = scale1
    s0 = np.min(scale)
    dj = np.log(scale[1]/scale[0])/np.log(2.)
    

    if (n1 == 1):
        variance = Y
    else:
        variance = np.std(Y)**2

    if (sigtest == -1): sigtest = 0
    if (lag1 == -1): lag1 = 0.0
    if (siglvl == -1): siglvl = 0.95
    if (mother == -1): mother = 'MORLET'

    mother = mother.upper()

    # get the appropriate parameters [see Table(2)]
    if (mother=='MORLET'):  #----------------------------------  Morlet
        if (param == -1): param = 6.
        k0 = param
        fourier_factor = (4.*np.pi)/(k0 + np.sqrt(2. + k0**2)) # Scale-->Fourier [Sec.3h]
        empir = [2.,-1,-1,-1]
        if (k0 == 6): empir[1:4]=[0.776,2.32,0.60]    
    elif (mother=='PAUL'):  #--------------------------------  Paul
        if (param == -1): param = 4.
        m = param
        fourier_factor = 4.*np.pi/(2.*m+1.)
        empir = [2.,-1,-1,-1]
        if (m == 4): empir[1:4]=[1.132,1.17,1.5] 
    elif (mother=='DOG'):  #---------------------------------  DOG
        if (param == -1): param = 2.
        m = param
        fourier_factor = 2.*np.pi*np.sqrt(2./(2.*m+1.))
        empir = [1.,-1,-1,-1]
        if (m == 2): empir[1:4] = [3.541,1.43,1.4]
        if (m == 6): empir[1:4] = [1.966,1.37,0.97]
    else:
        raise Exception("Mother must be one of MORLET,PAUL,DOG")

    period = scale*fourier_factor
    dofmin = empir[0]     # Degrees of freedom with no smoothing
    Cdelta = empir[1]     # reconstruction factor
    gamma_fac = empir[2]  # time-decorrelation factor
    dj0 = empir[3]        # scale-decorrelation factor

    freq = dt / period   # normalized frequency
    fft_theor = (1.-lag1**2) / (1.-2.*lag1*np.cos(freq*2.*np.pi)+lag1**2)  # [Eqn(16)]
    fft_theor = variance*fft_theor  # include time-series variance
    signif = fft_theor
    try:
        test=len(dof)
    except:
        if (dof == -1):
            dof = dofmin
        else:
            pass
    #
    if (sigtest == 0):    # no smoothing, DOF=dofmin [Sec.4]
        dof = dofmin
        chisquare = chi2.ppf(siglvl,dof)/dof
        signif = fft_theor*chisquare   # [Eqn(18)]
    elif (sigtest == 1):  # time-averaged significance
        try: 
            test=len(dof)
        except:
            dof=np.zeros((J1+1,))+dof
        truncate = dof < 1
        dof[truncate] = 1.
        dof = dofmin*np.sqrt(1. + (dof*dt/gamma_fac / scale)**2 )   # [Eqn(23)]
        truncate = dof < dofmin
        dof[truncate] = dofmin   # minimum DOF is dofmin
        for a1 in range(J1+1):
            chisquare = chi2.ppf(siglvl,dof[a1])/dof[a1]
            signif[a1] = fft_theor[a1]*chisquare
    elif (sigtest == 2):  # time-averaged significance
        if not (len(dof) == 2):
            raise Exception("DOF must be set to [S1,S2], the range of scale-averages'")
        if (Cdelta == -1):
            raise Exception('Cdelta & dj0 not defined for '+mother+' with param = '+str(param))
        s1 = dof[0]
        s2 = dof[1]
        avg = (scale >= s1) & (scale <= s2)  # scales between S1 & S2
        navg=np.sum(avg)
        if navg==0:
            raise Exception('No valid scales between '+str(s1)+' and '+str(s2))
        Savg = 1./np.sum(1 / scale[avg])    # [Eqn(25)]
        Smid = np.exp((np.log(s1)+np.log(s2))/2.)     # power-of-two midpoint
        dof = (dofmin*navg*Savg/Smid)*np.sqrt(1. + (navg*dj/dj0)**2)  # [Eqn(28)]
        fft_theor = Savg*np.sum(fft_theor[avg] / scale[avg])  # [Eqn(27)]#
        chisquare = chi2.ppf(siglvl,dof)/dof
        signif = (dj*dt/Cdelta/Savg)*fft_theor*chisquare    # [Eqn(26)]
    else:
        raise Exception('sigtest must be either 0, 1, or 2')

    return signif,fft_theor

# end of code