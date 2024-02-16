import pyomo.environ as pyo

def STATION_constr(m, scale):
 
    def STATION_mass_balance_rule(m, s, t):
        return m.inlet_w[s, t] == m.outlet_w[s, t]
    m.STATION_mass_balance = pyo.Constraint(
        m.Stations, m.Times, 
        rule = STATION_mass_balance_rule) 

    def STATION_pressure_ratio_rule(m, s, t):
        n_out = m.Arcs_NodeOUT[s]
        n_in = m.Arcs_NodeIN[s]
        pout = m.node_p[n_out, t]
        pin = m.node_p[n_in, t]
        return pin * m.compressor_beta[s, t] == pout
    m.STATION_pressure_ratio = pyo.Constraint(
        m.Stations, m.Times, 
        rule = STATION_pressure_ratio_rule) 

    def STATION_power_rule(m, s, t):
        w = m.inlet_w[s, t] * scale['w']
        P = m.compressor_P[s, t]
        beta = m.compressor_beta[s, t]
        eta = m.compressor_eta[s, t]
        cp = 'PLACEHOLDER'
        gamma = 'PLACEHOLDER'
        Tin =  'PLACEHOLDER'
        teta = 'PLACEHOLDER'
        dh = cp * Tin * (beta ** teta - 1)
        return P == (w * dh / eta) / scale['P']
    m.STATION_power_balance = pyo.Constraint(
        m.Stations, m.Times, 
        rule = STATION_power_rule)
    
    return m



