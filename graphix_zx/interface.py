from __future__ import annotations

from abc import ABC, abstractmethod
import uuid

import pyzx as zx


class PhysicalNode(ABC):
    @abstractmethod
    def __init__(self):
        raise NotImplementedError

    @abstractmethod
    def is_input(self):
        raise NotImplementedError

    @abstractmethod
    def is_output(self):
        raise NotImplementedError

    @abstractmethod
    def is_internal(self):
        raise NotImplementedError

    @abstractmethod
    def get_meas_plane(self):
        raise NotImplementedError

    @abstractmethod
    def get_meas_angle(self):
        raise NotImplementedError

    @abstractmethod
    def set_meas_plane(self, plane: str):
        raise NotImplementedError

    @abstractmethod
    def set_meas_angle(self, angle: float):
        raise NotImplementedError


# abstract class for graph state
# NOTE: this class just represents a graph state, not necessarily include optimization
class GraphState(ABC):
    @abstractmethod
    def __init__(self):
        pass

    # NOTE: input and output nodes are necessary because graph is open graph
    def input_nodes(self):
        return self.input_qubits

    def output_nodes(self):
        return self.output_qubits

    @abstractmethod
    def add_node(self, node: int):
        raise NotImplementedError

    @abstractmethod
    def add_edge(self, node1: int, node2: int):
        raise NotImplementedError

    @abstractmethod
    def set_meas_plane(self, node: int, plane: str):
        raise

    @abstractmethod
    def set_meas_angle(self, node: int, angle: float):
        raise NotImplementedError

    @abstractmethod
    def get_nodes(self):
        raise NotImplementedError

    @abstractmethod
    def get_edges(self):
        raise NotImplementedError

    @abstractmethod
    def get_meas_planes(self):
        raise NotImplementedError

    @abstractmethod
    def get_meas_angles(self):
        raise NotImplementedError


class ZXPhysicalNode(PhysicalNode):
    def __init__(self):
        self.is_input: bool = False
        self.is_output: bool = False
        self.is_internal: bool = False

    def is_input(self):
        return self.is_input

    def is_output(self):
        return self.is_output

    def is_internal(self):
        return self.is_internal

    def get_meas_plane(self):
        raise NotImplementedError

    def get_meas_angle(self):
        raise NotImplementedError

    def set_meas_plane(self, plane: str):
        raise NotImplementedError

    def set_meas_angle(self, angle: float):
        raise NotImplementedError

    def is_measurement_form(self):
        raise NotImplementedError

    # transform into XY, XZ, or YZ spider form described in Backens(2021)
    def to_measurement_form(self):
        raise NotImplementedError


# NOTE: for Arbitrary GraphState Construction permitted in MBQC
class ZXGraphState(zx.BaseGraph, GraphState):
    def __init__(self):
        super().__init__()

        # NOTE: macro node is composed of XY, XZ, or YZ physical nodes
        self.physical_nodes: dict[int, ZXPhysicalNode] = dict()

    def __add__(self, other):
        raise NotImplementedError

    def add_node(self, node: int):
        raise NotImplementedError

    def add_edge(self, node1: int, node2: int):
        raise NotImplementedError

    def set_meas_plane(self, node: int, plane: str):
        raise NotImplementedError

    def set_meas_angle(self, node: int, angle: float):
        raise NotImplementedError

    def get_nodes(self):
        raise NotImplementedError

    def get_edges(self):
        raise NotImplementedError

    def get_meas_planes(self):
        raise NotImplementedError

    def get_meas_angles(self):
        raise NotImplementedError


# NOTE: for Unitary Construction
class MBQCCircuit(ZXGraphState):
    def __init__(self):
        super().__init__()  # initialize of BaseGraph
        self.input_qubits = []
        self.output_qubits = []

    # gate concatenation
    def __add__(self, other):
        raise NotImplementedError

    # unit gate of XY plane
    def J(self, qubit: int, angle: float):
        """
        Apply a J gate to a qubit.
        """
        old_node = self.output_qubits[qubit]
        self.set_meas_angle(old_node, angle)
        new_node = gen_new_index()  # TODO: implement
        self.add_node(new_node)
        self.add_edge(old_node, new_node)
        self.output_qubits[qubit] = new_node
        # new_spider = self.add_vertex(
        # ty=zx.VertexType.Z, qubit=qubit, row=qubit, phase=0
        # )
        # self.add_edge((old_spider, new_spider), ty=zx.EdgeType.HADAMARD)

        # TODO: record gflow

    # TODO: unit gate of XZ and YZ planes
    def PhaseGadget(self, qubits: list[int], angle: float):
        target_nodes = [self.output_qubits[qubit] for qubit in qubits]
        new_node = gen_new_index()  # TODO: implement
        self.add_node(new_node)
        self.set_meas_angle(new_node, angle)
        self.set_meas_plane(new_node, "YZ")
        for node in target_nodes:
            self.add_edge(node, new_node)

    # vertical edge
    def CZ(self, qubit1: int, qubit2: int):
        """
        Apply a CZ gate between two qubits.
        """
        node1 = self.output_qubits[qubit1]
        node2 = self.output_qubits[qubit2]
        self.add_edge(node1, node2)
        # spider1 = self.output_qubits[qubit1]
        # spider2 = self.output_qubits[qubit2]
        # self.add_edge((spider1, spider2), ty=zx.EdgeType.HADAMARD)

    def Rx(self, qubit: int, phase: float):  # example
        self.J(qubit, 0)
        self.J(qubit, phase)

    def Rz(self, qubit: int, phase: float):
        self.J(qubit, phase)
        self.J(qubit, 0)

    def CNOT(self, qubit1: int, qubit2: int):
        self.J(qubit2, 0)
        self.CZ(qubit1, qubit2)
        self.J(qubit2, 0)


def gen_new_index():
    return uuid.uuid4().int


def visualize(graph: GraphState):
    if isinstance(graph, MBQCCircuit):
        # visualize based on the logical qubit path
        raise NotImplementedError
    else:
        raise NotImplementedError
