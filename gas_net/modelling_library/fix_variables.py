import pyomo.environ as pyo

#=========================================================================
""" FIX INPUTS """
#==============================================================================

def fix_exogenous_inputs(m, scale, Options, networkData, inputData):


    for k in ['pSource', 'wSource', 'wCons']:
        # define wheter to fix or not variable
        fix = True
        if k == 'wSource' or k == 'pSource':
            # ! wCons always fixed, INSERT RULE TO FIX EITHER pSOURCE OR wSOURCE
            fix = False
        
        # define scale factor (from SI base units)
        scale_factor = 1
        if k in ['wSource', 'wCons']:
            scale_factor = scale['w']
        elif k in ['pSource']:
            scale_factor = scale['p']
        # retrieve corresponding pyomo object and indices
        varobject = getattr(m, k)
        indices = list(varobject)
        # set values
        for indx in indices:      
            # find value 
            t = indx[-1] 
            compo0 = indx[0]
            # 2 levels dictionary: (component0, time)
            if 'Source' in k:
                # sources can be named differently in networkData and inputData dictionary
                source_name = networkData['Nodes'][compo0]["source"] 
                compo0 = compo0.replace(compo0, source_name)
            if len(indx) == 2:  
                value = inputData[k][compo0][t] 
            else:
                # 3 levels dictionary: (component0, component1, time) --> es. wCons
                compo1 = indx[1]
                value = inputData[k][compo0][compo1][t]
            # scale value
            value = value / scale_factor
            # set value in pyomo variable
            varobject[indx] = value                      
        # fix value
        if fix:
            varobject.fix() 

    return m

