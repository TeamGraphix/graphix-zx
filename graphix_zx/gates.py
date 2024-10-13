from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray


class UnitGateKind(Enum):
    """Enum class for gate kind"""

    J = auto()
    CZ = auto()
    PhaseGadget = auto()


class Gate(ABC):
    @abstractmethod
    def get_unit_gates(self) -> list[UnitGate]:
        raise NotImplementedError

    @abstractmethod
    def get_matrix(self) -> NDArray[np.complex128]:
        raise NotImplementedError


class UnitGate(Gate):
    @property
    @abstractmethod
    def kind(self) -> UnitGateKind:
        raise NotImplementedError


@dataclass(frozen=True)
class J(UnitGate):
    qubit: int
    angle: float

    @property
    def kind(self) -> UnitGateKind:
        return UnitGateKind.J

    def get_unit_gates(self) -> list[UnitGate]:
        return [self]

    def get_matrix(self) -> NDArray[np.complex128]:
        array: NDArray[np.complex128] = np.asarray(
            [[1, np.exp(1j * self.angle)], [1, -np.exp(1j * self.angle)]]
        ) / np.sqrt(2)
        return array


@dataclass(frozen=True)
class CZ(UnitGate):
    qubits: tuple[int, int]

    @property
    def kind(self) -> UnitGateKind:
        return UnitGateKind.CZ

    def get_unit_gates(self) -> list[UnitGate]:
        return [self]

    def get_matrix(self) -> NDArray:  # noqa: PLR6301 to align with pyright checks
        return np.asarray([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, -1]])


@dataclass(frozen=True)
class PhaseGadget(UnitGate):
    qubits: list[int]
    angle: float

    @property
    def kind(self) -> UnitGateKind:
        return UnitGateKind.PhaseGadget

    def get_unit_gates(self) -> list[UnitGate]:
        return [self]

    def get_matrix(self) -> NDArray[np.complex128]:
        def count_ones_in_binary(array: NDArray) -> NDArray[np.uint64]:
            count_ones = np.vectorize(lambda x: bin(x).count("1"))
            binary_array: NDArray[np.uint64] = count_ones(array)
            return binary_array

        index_array = np.arange(2 ** len(self.qubits))
        z_sign = (-1) ** count_ones_in_binary(index_array)
        return np.diag(np.exp(-1j * self.angle / 2 * z_sign))


# Macro gates


class MacroSingleGate(Gate):
    def get_matrix(self) -> NDArray[np.complex128]:
        matrix = np.eye(2, dtype=np.complex128)
        for unit_gate in self.get_unit_gates():
            matrix = unit_gate.get_matrix() @ matrix
        return matrix


class MacroTwoQubitGate(Gate):
    pass


class MacroMultiGate(Gate):
    pass


@dataclass(frozen=True)
class Identity(MacroSingleGate):
    qubit: int

    def get_unit_gates(self) -> list[UnitGate]:
        return [J(self.qubit, 0), J(self.qubit, 0)]


@dataclass(frozen=True)
class X(MacroSingleGate):
    qubit: int

    def get_unit_gates(self) -> list[UnitGate]:
        return [J(self.qubit, np.pi), J(self.qubit, 0)]


@dataclass(frozen=True)
class Y(MacroSingleGate):
    qubit: int

    def get_unit_gates(self) -> list[UnitGate]:
        return [
            J(self.qubit, np.pi / 2),
            J(self.qubit, np.pi),
            J(self.qubit, -np.pi / 2),
            J(self.qubit, 0),
        ]


@dataclass(frozen=True)
class Z(MacroSingleGate):
    qubit: int

    def get_unit_gates(self) -> list[UnitGate]:
        return [J(self.qubit, 0), J(self.qubit, np.pi)]


@dataclass(frozen=True)
class H(MacroSingleGate):
    qubit: int

    def get_unit_gates(self) -> list[UnitGate]:
        return [J(self.qubit, 0)]


@dataclass(frozen=True)
class S(MacroSingleGate):
    qubit: int

    def get_unit_gates(self) -> list[UnitGate]:
        return [J(self.qubit, 0), J(self.qubit, np.pi / 2)]


@dataclass(frozen=True)
class T(MacroSingleGate):
    qubit: int

    def get_unit_gates(self) -> list[UnitGate]:
        return [J(self.qubit, 0), J(self.qubit, np.pi / 4)]


@dataclass(frozen=True)
class Rx(MacroSingleGate):
    qubit: int
    angle: float

    def get_unit_gates(self) -> list[UnitGate]:
        return [
            J(self.qubit, self.angle),
            J(self.qubit, 0),
        ]


@dataclass(frozen=True)
class Ry(MacroSingleGate):
    qubit: int
    angle: float

    def get_unit_gates(self) -> list[UnitGate]:
        return [
            J(self.qubit, np.pi / 2),
            J(self.qubit, self.angle),
            J(self.qubit, -np.pi / 2),
            J(self.qubit, 0),
        ]


@dataclass(frozen=True)
class Rz(MacroSingleGate):
    qubit: int
    angle: float

    def get_unit_gates(self) -> list[UnitGate]:
        return [J(self.qubit, 0), J(self.qubit, self.angle)]


@dataclass(frozen=True)
class U3(MacroSingleGate):
    qubit: int
    angle1: float
    angle2: float
    angle3: float

    def get_unit_gates(self) -> list[UnitGate]:
        return [
            J(self.qubit, 0),
            J(self.qubit, -self.angle1),
            J(self.qubit, -self.angle2),
            J(self.qubit, -self.angle3),
        ]


@dataclass(frozen=True)
class CNOT(MacroMultiGate):
    control: int
    target: int

    def get_unit_gates(self) -> list[UnitGate]:
        return [
            J(self.target, 0),
            CZ((self.control, self.target)),
            J(self.target, 0),
        ]

    def get_matrix(self) -> NDArray:  # noqa: PLR6301
        return np.asarray([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]])


@dataclass(frozen=True)
class SWAP(MacroMultiGate):
    qubit1: int
    qubit2: int

    def get_unit_gates(self) -> list[UnitGate]:
        macro_gates = [
            CNOT(self.qubit1, self.qubit2),
            CNOT(self.qubit2, self.qubit1),
            CNOT(self.qubit1, self.qubit2),
        ]
        unit_gates: list[UnitGate] = []
        for macro_gate in macro_gates:
            unit_gates.extend(macro_gate.get_unit_gates())
        return unit_gates

    def get_matrix(self) -> NDArray:  # noqa: PLR6301
        return np.asarray(
            [
                [1, 0, 0, 0],
                [0, 0, 1, 0],
                [0, 1, 0, 0],
                [0, 0, 0, 1],
            ]
        )


@dataclass(frozen=True)
class CRz(MacroMultiGate):
    control: int
    target: int
    angle: float

    def get_unit_gates(self) -> list[UnitGate]:
        macro_gates = [
            Rz(self.target, self.angle / 2),
            CNOT(self.control, self.target),
            Rz(self.target, -self.angle / 2),
            CNOT(self.control, self.target),
        ]
        unit_gates: list[UnitGate] = []
        for macro_gate in macro_gates:
            unit_gates.extend(macro_gate.get_unit_gates())
        return unit_gates

    def get_matrix(self) -> NDArray:
        return np.asarray(
            [
                [1, 0, 0, 0],
                [0, np.exp(-1j * self.angle / 2), 0, 0],
                [0, 0, 1, 0],
                [0, 0, 0, np.exp(1j * self.angle / 2)],
            ]
        )


@dataclass(frozen=True)
class CRx(MacroMultiGate):
    control: int
    target: int
    angle: float

    def get_unit_gates(self) -> list[UnitGate]:
        macro_gates = [
            Rz(self.target, np.pi / 2),
            CNOT(self.control, self.target),
            U3(self.target, -self.angle / 2, 0, 0),
            CNOT(self.control, self.target),
            U3(self.target, self.angle / 2, -np.pi / 2, 0),
        ]
        unit_gates: list[UnitGate] = []
        for macro_gate in macro_gates:
            unit_gates.extend(macro_gate.get_unit_gates())
        return unit_gates

    def get_matrix(self) -> NDArray:
        return np.asarray(
            [
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, np.cos(self.angle), -1j * np.sin(self.angle)],
                [0, -1j * np.sin(self.angle), 0, np.cos(self.angle)],
            ]
        )


@dataclass(frozen=True)
class CU3(MacroMultiGate):
    control: int
    target: int
    angle1: float
    angle2: float
    angle3: float

    def get_unit_gates(self) -> list[UnitGate]:
        macro_gates = [
            Rz(self.control, self.angle3 / 2 + self.angle2 / 2),
            Rz(self.target, self.angle3 / 2 - self.angle2 / 2),
            CNOT(self.control, self.target),
            U3(self.target, -self.angle1 / 2, 0, -(self.angle2 + self.angle3) / 2),
            CNOT(self.control, self.target),
            U3(self.target, self.angle1 / 2, self.angle2, 0),
        ]
        unit_gates: list[UnitGate] = []
        for macro_gate in macro_gates:
            unit_gates.extend(macro_gate.get_unit_gates())
        return unit_gates

    def get_matrix(self) -> NDArray:
        return np.asarray(
            [
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [
                    0,
                    0,
                    np.cos(self.angle1),
                    -np.exp(1j * self.angle3) * np.sin(self.angle1),
                ],
                [
                    0,
                    0,
                    np.exp(1j * self.angle2) * np.sin(self.angle1),
                    np.exp(1j * (self.angle2 + self.angle3)) * np.cos(self.angle1),
                ],
            ]
        )


@dataclass(frozen=True)
class CCZ(MacroMultiGate):
    control1: int
    control2: int
    target: int

    def get_unit_gates(self) -> list[UnitGate]:
        macro_gates = [
            CRz(self.control2, self.target, np.pi / 2),
            CNOT(self.control1, self.control2),
            CRz(self.control2, self.target, -np.pi / 2),
            CNOT(self.control1, self.control2),
            CRz(self.control1, self.target, np.pi / 2),
        ]
        unit_gates: list[UnitGate] = []
        for macro_gate in macro_gates:
            unit_gates.extend(macro_gate.get_unit_gates())
        return unit_gates

    def get_matrix(self) -> NDArray:  # noqa: PLR6301
        return np.asarray(
            [
                [1, 0, 0, 0, 0, 0, 0, 0],
                [0, 1, 0, 0, 0, 0, 0, 0],
                [0, 0, 1, 0, 0, 0, 0, 0],
                [0, 0, 0, 1, 0, 0, 0, 0],
                [0, 0, 0, 0, 1, 0, 0, 0],
                [0, 0, 0, 0, 0, 1, 0, 0],
                [0, 0, 0, 0, 0, 0, 1, 0],
                [0, 0, 0, 0, 0, 0, 0, -1],
            ]
        )


@dataclass(frozen=True)
class Toffoli(MacroMultiGate):
    control1: int
    control2: int
    target: int

    def get_unit_gates(self) -> list[UnitGate]:
        macro_gates = [
            H(self.target),
            CRz(self.control2, self.target, np.pi / 2),
            CNOT(self.control1, self.control2),
            CRz(self.control2, self.target, -np.pi / 2),
            CNOT(self.control1, self.control2),
            CRz(self.control1, self.target, np.pi / 2),
            H(self.target),
        ]
        unit_gates: list[UnitGate] = []
        for macro_gate in macro_gates:
            unit_gates.extend(macro_gate.get_unit_gates())
        return unit_gates

    def get_matrix(self) -> NDArray:  # noqa: PLR6301
        return np.asarray(
            [
                [1, 0, 0, 0, 0, 0, 0, 0],
                [0, 1, 0, 0, 0, 0, 0, 0],
                [0, 0, 1, 0, 0, 0, 0, 0],
                [0, 0, 0, 1, 0, 0, 0, 0],
                [0, 0, 0, 0, 1, 0, 0, 0],
                [0, 0, 0, 0, 0, 1, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 1],
                [0, 0, 0, 0, 0, 0, 1, 0],
            ]
        )
