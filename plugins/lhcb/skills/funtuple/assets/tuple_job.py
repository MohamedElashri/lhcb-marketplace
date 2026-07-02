"""Minimal Run 3 FunTuple configuration for a persisted HLT2 selection."""

import FunTuple.functorcollections as FC
from DaVinci import Options, make_config
from DaVinci.algorithms import create_lines_filter
from FunTuple import FunTuple_Particles as Funtuple
from PyConf.reading import get_particles

LINE = "Hlt2B2OC_BdToDsmPi_DsmToKpKmPim"


def main(options: Options):
    particles = get_particles(f"/Event/HLT2/{LINE}/Particles")
    fields = {
        "B": "[B0 -> (D_s- -> K- K+ pi-) pi+]CC",
        "Ds": "[B0 -> ^(D_s- -> K- K+ pi-) pi+]CC",
        "BachelorPi": "[B0 -> (D_s- -> K- K+ pi-) ^pi+]CC",
    }
    variables = {
        "B": FC.Kinematics(),
        "Ds": FC.Kinematics(),
        "BachelorPi": FC.Kinematics() + FC.ParticleID(),
    }
    event_variables = FC.EventInfo()
    tuple_alg = Funtuple(
        name="BToDsPiTuple",
        tuple_name="DecayTree",
        fields=fields,
        variables=variables,
        event_variables=event_variables,
        inputs=particles,
    )
    algorithms = [
        create_lines_filter(name=f"PreFilter_{LINE}", lines=[LINE]),
        tuple_alg,
    ]
    return make_config(options, algorithms)
