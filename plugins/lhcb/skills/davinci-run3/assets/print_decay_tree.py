"""Minimal Run 3 DaVinci configuration for inspecting a persisted selection."""

from DaVinci import Options, make_config
from DaVinci.algorithms import create_lines_filter
from PyConf.Algorithms import PrintDecayTree
from PyConf.reading import get_particles

LINE = "Hlt2B2OC_BdToDsmPi_DsmToKpKmPim"


def main(options: Options):
    particles = get_particles(f"/Event/HLT2/{LINE}/Particles")
    algorithms = [
        create_lines_filter(name=f"PreFilter_{LINE}", lines=[LINE]),
        PrintDecayTree(name="PrintSelectedDecay", Input=particles),
    ]
    return make_config(options, algorithms)
