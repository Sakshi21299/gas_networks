import pyomo.environ as pyo

def VALVE_constr(m):
 
    def VALVE_mass_balance_rule(m, s, t):
        return m.inlet_w[s, t] == m.outlet_w[s, t]
    m.VALVE_mass_balance = pyo.Constraint(
        m.Valves, m.Times, 
        rule = VALVE_mass_balance_rule)

    def VALVE_pressure_flow_rule(m, s, t):
        # this rule ensures: if dp < 0 --> w = 0
        w = m.inlet_w[s, t]
        nout = m.Arcs_NodeOUT[s]
        pout = m.node_p[nout, t]
        nin = m.Arcs_NodeIN[s]
        pin = m.node_p[nin, t]
        dp = (pin - pout)  
        return w * dp >= 0
    m.VALVE_pressure_flow = pyo.Constraint(
        m.Valves, m.Times,
        rule = VALVE_pressure_flow_rule)

    m.inlet_w.setlb(0)

    return m




