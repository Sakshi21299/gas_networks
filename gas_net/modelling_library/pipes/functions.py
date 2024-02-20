
#=============================================================================
""" FUNCTIONS - PIPE FINITE VOLUMES """
#==============================================================================


def Pipe_GasDensity(
        m, scale, p, vol, t, N, 
        calc = True):
    ''' 
    Evaluate gas density in pipes finite volumes ''' 
    # equation of state
    if calc:
        # gas parameters 
        Tgas = m.Gas[p,"Tgas"]
        MM = m.Gas[p,"MMgas"]
        Zavrg = m.Gas[p,"Z"]
        # equation #
        press = Pipe_Pressure(m, p, vol, t, N)*scale["p"]  
        rho = press / (8314 / MM * Tgas * Zavrg)
        return rho 
    # pyomo variable
    else:
        rho = m.pipe_rho[p, vol, t]
        return rho 

def Pipe_Pressure(
        m, p, vol, t, N):
    ''' 
    Evaluate pressure in pipes finite volumes ''' 
    # find pressure of Finite Volume of pipe
    start = 1
    end = N+1    
    # pressures in the middle of the pipes
    if vol != start and vol != end:
        press = m.interm_p[p, vol, t] 
    # pressure at the outlet
    elif vol == end:
        n_out = m.Arcs_NodeOUT[p]
        press = m.node_p[n_out, t]
    # pressure at the inlet
    elif vol == start:
        n_in = m.Arcs_NodeIN[p]
        press = m.node_p[n_in, t] 
    return press

def Pipe_MassFlow(
        m, p, vol, t, N):
    ''' 
    Evaluate mass flow rate in pipes finite volumes ''' 
    # find pressure of Finite Volume of pipe
    start = 1
    end = N    
    # flow at the inlet   
    if vol == start:
        w = m.inlet_w[p, t] 
    # flow at the outlet
    elif vol == end:
        w = m.outlet_w[p, t] 
    # flow in the middle of the pipes 
    else:
        w = m.interm_w[p, vol, t] 
    return w

def Pipe_DerMass(
        m, p, vol, t, N, V, scale, dt
        ):  
    
    ''' 
    Evaluate derivative term in mass balance.
    Remark: density is evaluated on the staggered grid (next volume) ''' 
    
    t_prev = m.Times.prev(t)
    # density
    rho = Pipe_GasDensity(m, scale, p, vol+1, t, N, calc = False)
    # density at previous time step
    rho_prev = Pipe_GasDensity(m, scale, p, vol+1, t_prev, N, calc = False)                                   
    dMdt = ((rho - rho_prev)*V/ (N-1)) / (dt)                   
    return dMdt    
