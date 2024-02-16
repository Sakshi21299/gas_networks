import pyomo.environ as pyo

def OBJ_compressor_power(m, Opt):
    dt = Opt['dt']
    def ObjFun(m):
        Obj = sum(m.compressor[s, t]*dt for s in m.Stations for t in m.Times)
        return Obj / 1000
    m.ObjFun = pyo.Objective(rule = ObjFun, sense = 1)
    return m

