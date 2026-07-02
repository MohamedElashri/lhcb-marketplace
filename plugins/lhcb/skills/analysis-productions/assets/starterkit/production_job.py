"""Minimal Run 3 Analysis Production for the public Starterkit sample."""

import FunTuple.functorcollections as FC
from DaVinci import Options, make_config
from DaVinci.algorithms import create_lines_filter
from FunTuple import FunTuple_Particles as Funtuple
from PyConf.reading import get_particles, get_pvs
from RecoConf.event_filters import require_pvs

LINE = "Hlt2B2OC_BdToDsmPi_DsmToKpKmPim"


def main(options: Options):
    particles = get_particles(f"/Event/Turbo/{LINE}/Particles")
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
    tuple_alg = Funtuple(
        name="BToDsPiTuple",
        tuple_name="DecayTree",
        fields=fields,
        variables=variables,
        event_variables=FC.EventInfo(),
        inputs=particles,
    )
    algorithms = [
        create_lines_filter(name=f"PreFilter_{LINE}", lines=[LINE]),
        require_pvs(get_pvs()),
        tuple_alg,
    ]
    return make_config(options, {LINE: algorithms})
