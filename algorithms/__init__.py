from .fcfs import FCFSDispatcher
from .sstf import SSTFDispatcher
from .scan import SCANDispatcher
from .look import LOOKDispatcher

ALGORITHMS: dict[str, type] = {
    "FCFS": FCFSDispatcher,
    "SSTF": SSTFDispatcher,
    "SCAN": SCANDispatcher,
    "LOOK": LOOKDispatcher,
}
