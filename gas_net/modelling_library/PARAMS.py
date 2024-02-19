import pyomo.environ as pyo

#==============================================================================
""" PARAMETERS """
#==============================================================================


############################### GAS ######################################
##########################################################################

def PIPE_gas_params(m, networkData):
    Pipes = networkData['Pipes']

    # GAS PROPERTIES
    Gas = {}
    for arc in m.Pipes.data():   
        for par in ["MMgas", "Tgas", "Z"]:      
            Gas[(arc, par)] = Pipes[arc][par]

    m.Gas = pyo.Param(Gas.keys(), initialize = Gas, within = pyo.Reals) 

    return m

######################### GEOMETRY ########################################
###########################################################################

def PIPE_geom_params(m, networkData):
    Pipes = networkData['Pipes']
    # number of finite volumes per pipe
    Nvol = {p: Pipes[p]['Nvol'] for p in m.Pipes}
    m.Nvol = pyo.Param(m.Pipes, initialize=Nvol, default=2, within = pyo.Integers)
    # area of the pipe
    A = {p: Pipes[p]['A'] for p in m.Pipes}
    m.Area = pyo.Param(m.Pipes, initialize=A, within = pyo.NonNegativeReals)
    # lenght of the pipe
    L = {p: Pipes[p]['length'] for p in m.Pipes}
    m.Length = pyo.Param(m.Pipes, initialize=L, within = pyo.NonNegativeReals)
    # diameter of the pipe
    D = {p: Pipes[p]['diameter'] for p in m.Pipes}
    m.Diam = pyo.Param(m.Pipes, initialize=D, within = pyo.NonNegativeReals)
    # roughness of the pipe
    rough = {p: Pipes[p]['roughness'] for p in m.Pipes}
    m.Roughness = pyo.Param(m.Pipes, initialize=rough, within = pyo.NonNegativeReals)
    # wet perimeter of the pipe (omega = pi*D)
    omega = {p: Pipes[p]['omega'] for p in m.Pipes}
    m.Omega = pyo.Param(m.Pipes, initialize=omega, within = pyo.NonNegativeReals)
    return m

######################### FLOW REVERSAL ########################################
###########################################################################


def PIPE_smoothing_params(m, eps):
    m.eps = pyo.Param(initialize=eps, default=1e-4,mutable=True) # flow reversals smoothing
    return m