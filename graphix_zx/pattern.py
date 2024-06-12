from __future__ import annotations
import networkx as nx
from interface import GraphState
from focus_flow import (
    GFlow,
    topological_sort_kahn,
    construct_DAG,
    oddneighbors,
)
from command import N, E, M, X, Z, Pattern


# extended MBQC
def generate_M(
    node: int,
    meas_plane: str,
    meas_angle: float,
    x_correction: list[int],
    z_correction: list[int],
) -> M:
    if meas_plane == "XY":
        s_domain = x_correction
        t_domain = z_correction
    elif meas_plane == "XZ":
        s_domain = x_correction.extend(z_correction)
        t_domain = x_correction
    elif meas_plane == "YZ":
        s_domain = z_correction
        t_domain = x_correction
    return M(
        node=node,
        plane=meas_plane,
        angle=meas_angle,
        s_domain=s_domain,
        t_domain=t_domain,
    )


# generate signal lists
def generate_corrections(graph: GraphState, gflow: GFlow) -> tuple[list[int], list[int]]:
    x_corrections: dict[str, list[int]] = {node: list() for node in graph.nodes}
    z_corrections: dict[str, list[int]] = {node: list() for node in graph.nodes}
    for node, g in gflow.items():
        odd_g = oddneighbors(g, graph)
        for correction in g:
            x_corrections[correction].append(node)
        for correction in odd_g:
            z_corrections[correction].append(node)

    # remove itself
    for node in gflow.keys():
        x_corrections[node] = list(set(x_corrections[node]) - {node})
        z_corrections[node] = list(set(z_corrections[node]) - {node})

    return x_corrections, z_corrections


# generate standardized pattern from underlying graph and gflow
def transpile(
    graph: GraphState,
    input_nodes: list[int],
    output_nodes: list[int],
    gflow: GFlow,
    meas_planes: dict[int, str],
    meas_angles: dict[int, float],
) -> Pattern:
    # TODO : check the validity of the gflow

    internal_nodes = set(graph.nodes) - set(input_nodes) - set(output_nodes)

    # generate corrections
    x_corrections, z_corrections = generate_corrections(graph, gflow)

    dag = construct_DAG(gflow, graph)
    topo_order = topological_sort_kahn(dag)

    pattern = Pattern(input_nodes=input_nodes)
    pattern.extend([N(node=node) for node in internal_nodes])
    pattern.extend([N(node=node) for node in output_nodes])
    pattern.extend([E(nodes=edge) for edge in graph.edges])
    pattern.extend(
        [
            generate_M(
                node,
                meas_planes[node],
                meas_angles[node],
                x_corrections[node],
                z_corrections[node],
            )
            for node in topo_order
            if node not in output_nodes
        ]
    )
    pattern.extend([X(node=node, domain=x_corrections[node]) for node in output_nodes])
    pattern.extend([Z(node=node, domain=z_corrections[node]) for node in output_nodes])
    # TODO: add Clifford commands on the output nodes

    return pattern


def transpile_from_subgraphs(
    subgraphs: list[GraphState],
    input_nodes: list[int],
    output_nodes: list[int],
    gflow: GFlow,
    meas_planes: dict[int, str],
    meas_angles: dict[int, float],
) -> Pattern:
    pattern = Pattern(input_nodes=input_nodes)
    for subgraph in subgraphs:
        sub_input_nodes = subgraph.input_nodes  # TODO: define input_nodes
        sub_output_nodes = subgraph.output_nodes  # TODO: define output_nodes

        sub_internal_nodes = set(subgraph.nodes) - set(sub_input_nodes) - set(sub_output_nodes)
        sub_gflow = {node: gflow[node] for node in set(sub_input_nodes) | sub_internal_nodes}
        sub_meas_planes = {node: meas_planes[node] for node in set(sub_input_nodes) | sub_internal_nodes}
        sub_meas_angles = {node: meas_angles[node] for node in set(sub_input_nodes) | sub_internal_nodes}

        sub_pattern = transpile(
            subgraph,
            sub_input_nodes,
            sub_output_nodes,
            sub_gflow,
            sub_meas_planes,
            sub_meas_angles,
        )

        pattern += sub_pattern

    return pattern
