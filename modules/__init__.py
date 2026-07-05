"""THE MODULE REGISTRY.

This is the only file you edit when adding a new module. Import the class and
append an instance to the list. The order here is the order in the sidebar.
"""
from typing import List
from modules.base_module import BaseModule
from modules.home_dashboard.home_module import HomeDashboardModule
from modules.global_search.search_module import GlobalSearchModule
from modules.boot_simulator.boot_module import BootSimulatorModule
from modules.process_explorer.process_module import ProcessExplorerModule
from modules.service_explorer.service_module import ServiceExplorerModule
from modules.driver_explorer.driver_module import DriverExplorerModule
from modules.registry_explorer.registry_module import RegistryExplorerModule
from modules.memory_explorer.memory_module import MemoryExplorerModule
from modules.network_explorer.network_module import NetworkExplorerModule
from modules.auth_explorer.auth_module import AuthExplorerModule
from modules.proctree_explorer.proctree_module import ProcTreeExplorerModule
from modules.attack_simulator.attack_module import AttackSimulatorModule
from modules.defense_simulator.defense_module import DefenseSimulatorModule
from modules.edr_console.edr_module import EDRConsoleModule
from modules.soc_workspace.soc_module import SOCWorkspaceModule
from modules.learning_center.learning_module import LearningCenterModule


def get_registered_modules() -> List[BaseModule]:
    return [
        HomeDashboardModule(),
        GlobalSearchModule(),
        BootSimulatorModule(),
        ProcessExplorerModule(),
        ServiceExplorerModule(),
        DriverExplorerModule(),
        RegistryExplorerModule(),
        MemoryExplorerModule(),
        NetworkExplorerModule(),
        AuthExplorerModule(),
        ProcTreeExplorerModule(),
        AttackSimulatorModule(),
        DefenseSimulatorModule(),
        EDRConsoleModule(),
        SOCWorkspaceModule(),
        LearningCenterModule(),
    ]
