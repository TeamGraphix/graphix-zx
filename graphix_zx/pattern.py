from __future__ import annotations

from abc import ABC, abstractmethod

import dataclasses

from graphix_zx.command import Command, CommandKind, N, E, M, C, X, Z


class NodeAlreadyPreparedError(Exception):
    def __init__(self, node: int):
        self.__node = node

    @property
    def node(self):
        return self.__node

    def __str__(self) -> str:
        return f"Node already prepared: {self.__node}"


class BasePattern(ABC):
    def __len__(self):
        return len(self.get_commands())

    def __iter__(self):
        return iter(self.get_commands())

    def __getitem__(self, index):
        return self.get_commands()[index]

    @abstractmethod
    def get_input_nodes(self):
        raise NotImplementedError

    @abstractmethod
    def get_output_nodes(self):
        raise NotImplementedError

    @abstractmethod
    def get_q_indices(self):
        raise NotImplementedError

    @abstractmethod
    def get_commands(self):
        raise NotImplementedError

    @abstractmethod
    def calc_max_space(self):
        raise NotImplementedError

    @abstractmethod
    def is_runnable(self):
        raise NotImplementedError

    @abstractmethod
    def is_deterministic(self):
        raise NotImplementedError


@dataclasses.dataclass(frozen=True)
class ImmutablePattern(BasePattern):
    input_nodes: set[int]
    output_nodes: set[int]
    q_indices: dict[int, int]
    seq: list[Command]
    runnable: bool = False
    deterministic: bool = False

    def get_input_nodes(self):
        return set(self.input_nodes)

    def get_output_nodes(self):
        return set(self.output_nodes)

    def get_q_indices(self):
        return dict(self.q_indices)

    def get_commands(self):
        return self.seq

    def calc_max_space(self):
        nodes = len(self.input_nodes)
        max_nodes = nodes
        for cmd in self.seq:
            if cmd.kind == CommandKind.N:
                nodes += 1
            elif cmd.kind == CommandKind.M:
                nodes -= 1
            if nodes > max_nodes:
                max_nodes = nodes
        return max_nodes

    def is_runnable(self):
        return self.runnable

    def is_deterministic(self):
        return self.deterministic


class MutablePattern(BasePattern):
    def __init__(
        self,
        input_nodes: set[int] | None = None,
        q_indices: dict[int, int] | None = None,
    ):
        if input_nodes is None:
            input_nodes = set()
        self.__input_nodes: set[int] = set(input_nodes)  # input nodes (list() makes our own copy of the list)
        self.__Nnode: int = len(input_nodes)  # total number of nodes in the graph state

        self.__seq: list[Command] = []
        # output nodes are initially input nodes, since none are measured yet
        self.__output_nodes: set[int] = set(self.__input_nodes)

        if q_indices is None:
            q_indices = dict()
            _count = 0
            for input_node in input_nodes:
                q_indices[input_node] = _count
                _count += 1

        self.__q_indices: dict[int, int] = q_indices  # qubit index. used for simulation

        self.__runnable: bool = False
        self.__deterministic: bool = False

    def add(self, cmd: Command):
        if isinstance(cmd, N):
            if cmd.node in self.__output_nodes:
                raise NodeAlreadyPreparedError(cmd.node)
            self.__Nnode += 1
            self.__output_nodes |= {cmd.node}
            self.__q_indices[cmd.node] = cmd.q_index
        elif isinstance(cmd, M):
            self.__output_nodes -= {cmd.node}
        self.__seq.append(cmd)

        # runnablility and determinism are not guaranteed after adding a command
        self.__runnable = False
        self.__deterministic = False

    def extend(self, cmds: list[Command]):
        for cmd in cmds:
            self.add(cmd)

    def clear(self):
        self.__Nnode = len(self.__input_nodes)
        self.__seq = []
        self.__output_nodes = set(self.__input_nodes)

    def replace(self, cmds: list[Command], input_nodes: set[int] | None = None):
        if input_nodes is not None:
            self.__input_nodes = set(input_nodes)
        self.clear()
        self.extend(cmds)

    # should support immutable pattern as well?
    def append_pattern(self, pattern: MutablePattern):
        common_nodes = self.get_nodes() & pattern.get_nodes()
        border_nodes = self.get_output_nodes() & pattern.get_input_nodes()

        if common_nodes != border_nodes:
            raise ValueError("Patterns are not compatible")

        new_input_nodes = self.get_input_nodes() | (pattern.get_input_nodes() - common_nodes)
        new_input_q_indices = dict()
        for node in new_input_nodes:
            try:
                new_input_q_indices[node] = self.__q_indices[node]
            except KeyError:
                new_input_q_indices[node] = pattern.get_q_indices()[node]

        new_pattern = MutablePattern(input_nodes=new_input_nodes, q_indices=new_input_q_indices)
        for cmd in self.get_commands():
            new_pattern.add(cmd)

        for cmd in pattern.get_commands():
            new_pattern.add(cmd)

        if self.is_runnable() and pattern.is_runnable():
            new_pattern.mark_runnable()

        if self.is_deterministic() and pattern.is_deterministic():
            new_pattern.mark_deterministic()

        return new_pattern

    def get_input_nodes(self):
        return set(self.__input_nodes)

    def get_output_nodes(self):
        return set(self.__output_nodes)

    def get_q_indices(self):
        return dict(self.__q_indices)

    def get_nodes(self):
        nodes = set()
        for cmd in self.__seq:
            if cmd.kind == CommandKind.N:
                nodes |= {cmd.node}
        return nodes

    def get_commands(self):
        return self.__seq

    def calc_max_space(self):
        nodes = len(self.get_input_nodes())
        max_nodes = nodes
        for cmd in self.__seq:
            if cmd.kind == CommandKind.N:
                nodes += 1
            elif cmd.kind == CommandKind.M:
                nodes -= 1
            if nodes > max_nodes:
                max_nodes = nodes
        return max_nodes

    def get_space_list(self):
        nodes = len(self.get_input_nodes())
        space_list = [nodes]
        for cmd in self.__seq:
            if cmd.kind == CommandKind.N:
                nodes += 1
                space_list.append(nodes)
            elif cmd.kind == CommandKind.M:
                nodes -= 1
                space_list.append(nodes)
        return space_list

    def get_meas_planes(self):
        meas_plane = dict()
        for cmd in self.__seq:
            if cmd.kind == CommandKind.M:
                mplane = cmd.plane
                meas_plane[cmd.node] = mplane
        return meas_plane

    def get_meas_angles(self):
        angles = {}
        for cmd in self.__seq:
            if cmd.kind == CommandKind.M:
                angles[cmd.node] = cmd.angle
        return angles

    def is_runnable(self):
        return self.__runnable

    def is_deterministic(self):
        return self.__deterministic

    # Mark the pattern as runnable. Called where the pattern is guaranteed to be runnable
    def mark_runnable(self):
        self.__runnable = True

    # Mark the pattern as deterministic. Called where flow preservation is guaranteed
    def mark_deterministic(self):
        self.__deterministic = True

    def freeze(self) -> ImmutablePattern:
        return ImmutablePattern(
            input_nodes=self.__input_nodes,
            output_nodes=self.__output_nodes,
            q_indices=self.__q_indices,
            seq=self.__seq,
            runnable=self.__runnable,
            deterministic=self.__deterministic,
        )

    def standardize(self):
        raise NotImplementedError

    def shift_signals(self):
        raise NotImplementedError

    def pauli_simplification(self):
        raise NotImplementedError


def is_standardized(pattern: BasePattern) -> bool:
    standardized = True
    standardized_order = [
        CommandKind.N,
        CommandKind.E,
        CommandKind.M,
        CommandKind.X,
        CommandKind.Z,
        CommandKind.C,
    ]
    current_cmd_kind = CommandKind.N
    for cmd in pattern:
        if cmd.kind == current_cmd_kind:
            continue
        if cmd.kind not in standardized_order:
            raise ValueError(f"Unknown command kind: {cmd.kind}")
        if standardized_order.index(cmd.kind) < standardized_order.index(current_cmd_kind):
            standardized = False
            break
        current_cmd_kind = cmd.kind
    return standardized


def is_runnable(pattern: BasePattern) -> bool:
    raise NotImplementedError


# NOTE: generally, difficult to prove that a pattern is deterministic
def is_deterministic(pattern: BasePattern) -> bool:
    raise NotImplementedError


def print_pattern(pattern: BasePattern, lim: int = 40, cmd_filter: list[CommandKind] | None = None):
    if len(pattern) < lim:
        nmax = len(pattern)
    else:
        nmax = lim
    if cmd_filter is None:
        cmd_filter = [
            CommandKind.N,
            CommandKind.E,
            CommandKind.M,
            CommandKind.X,
            CommandKind.Z,
            CommandKind.C,
        ]
    count = 0
    i = -1
    while count < nmax:
        i = i + 1
        if i == len(pattern):
            break
        if pattern[i].kind == CommandKind.N and (CommandKind.N in cmd_filter):
            count += 1
            print(f"N, node = {pattern[i].node}")
        elif pattern[i].kind == CommandKind.E and (CommandKind.E in cmd_filter):
            count += 1
            print(f"E, nodes = {pattern[i].nodes}")
        elif pattern[i].kind == CommandKind.M and (CommandKind.M in cmd_filter):
            count += 1
            print(
                f"M, node = {pattern[i].node}, "
                + f"plane = {pattern[i].plane}, angle(pi) = {pattern[i].angle}, "
                + f"s-domain = {pattern[i].s_domain}, t_domain = {pattern[i].t_domain}"
            )
        elif pattern[i].kind == CommandKind.X and (CommandKind.X in cmd_filter):
            count += 1
            print(f"X byproduct, node = {pattern[i].node}, domain = {pattern[i].domain}")
        elif pattern[i].kind == CommandKind.Z and (CommandKind.Z in cmd_filter):
            count += 1
            print(f"Z byproduct, node = {pattern[i].node}, domain = {pattern[i].domain}")
        elif pattern[i].kind == CommandKind.C and (CommandKind.C in cmd_filter):
            count += 1
            print(f"Clifford, node = {pattern[i].node}, Clifford index = {pattern[i].cliff_index}")
        else:
            print(f"Command {pattern[i].kind} not recognized")

    if len(pattern) > i + 1:
        print(f"{len(pattern)-lim} more commands truncated. Change lim argument of print_pattern() to show more")
