"""Tests for the GraphState class."""

from __future__ import annotations

import numpy as np
import pytest

from graphix_zx.common import Plane, PlannerMeasBasis
from graphix_zx.graphstate import GraphState, bipartite_edges


@pytest.fixture
def graph() -> GraphState:
    """Generate an empty GraphState object.

    Returns
    -------
    GraphState: An empty GraphState object.
    """
    return GraphState()


def test_add_physical_node(graph: GraphState) -> None:
    """Test adding a physical node to the graph."""
    node_index = graph.add_physical_node()
    assert node_index in graph.physical_nodes
    assert graph.num_physical_nodes == 1


def test_add_physical_node_input_output(graph: GraphState) -> None:
    """Test adding a physical node as input and output."""
    node_index = graph.add_physical_node()
    q_index = graph.set_input(node_index)
    graph.set_output(node_index, q_index)
    assert node_index in graph.input_node_indices
    assert node_index in graph.output_node_indices
    assert graph.input_node_indices[node_index] == q_index
    assert graph.output_node_indices[node_index] == q_index


def test_ensure_node_exists_raises(graph: GraphState) -> None:
    """Test ensuring a node exists in the graph."""
    with pytest.raises(ValueError, match="Node does not exist node=1"):
        graph.ensure_node_exists(1)


def test_ensure_node_exists(graph: GraphState) -> None:
    """Test ensuring a node exists in the graph."""
    node_index = graph.add_physical_node()
    graph.ensure_node_exists(node_index)


def test_get_neighbors(graph: GraphState) -> None:
    """Test getting the neighbors of a node in the graph."""
    node_index1 = graph.add_physical_node()
    node_index2 = graph.add_physical_node()
    node_index3 = graph.add_physical_node()
    graph.add_physical_edge(node_index1, node_index2)
    graph.add_physical_edge(node_index2, node_index3)
    assert graph.get_neighbors(node_index1) == {node_index2}
    assert graph.get_neighbors(node_index2) == {node_index1, node_index3}
    assert graph.get_neighbors(node_index3) == {node_index2}


def test_add_physical_edge(graph: GraphState) -> None:
    """Test adding a physical edge to the graph."""
    node_index1 = graph.add_physical_node()
    node_index2 = graph.add_physical_node()
    graph.add_physical_edge(node_index1, node_index2)
    assert (node_index1, node_index2) in graph.physical_edges or (node_index2, node_index1) in graph.physical_edges
    assert graph.num_physical_edges == 1


def test_add_duplicate_physical_edge(graph: GraphState) -> None:
    """Test adding a duplicate physical edge to the graph."""
    node_index1 = graph.add_physical_node()
    node_index2 = graph.add_physical_node()
    graph.add_physical_edge(node_index1, node_index2)
    with pytest.raises(ValueError, match=f"Edge already exists node1={node_index1}, node2={node_index2}"):
        graph.add_physical_edge(node_index1, node_index2)


def test_add_edge_with_nonexistent_node(graph: GraphState) -> None:
    """Test adding an edge with a nonexistent node to the graph."""
    node_index1 = graph.add_physical_node()
    with pytest.raises(ValueError, match="Node does not exist node=2"):
        graph.add_physical_edge(node_index1, 2)


def test_remove_physical_node_with_nonexistent_node(graph: GraphState) -> None:
    """Test removing a nonexistent physical node from the graph."""
    with pytest.raises(ValueError, match="Node does not exist node=1"):
        graph.remove_physical_node(1)


def test_remove_physical_node_with_input_removal(graph: GraphState) -> None:
    """Test removing an input node from the graph"""
    node_index = graph.add_physical_node()
    graph.set_input(node_index)
    with pytest.raises(ValueError, match="The input node cannot be removed"):
        graph.remove_physical_node(node_index)


def test_remove_physical_node(graph: GraphState) -> None:
    """Test removing a physical node from the graph."""
    node_index = graph.add_physical_node()
    graph.remove_physical_node(node_index)
    assert node_index not in graph.physical_nodes
    assert graph.num_physical_nodes == 0


def test_remove_physical_node_from_minimal_graph(graph: GraphState) -> None:
    """Test removing a physical node from the graph with edges."""
    node_index1 = graph.add_physical_node()
    node_index2 = graph.add_physical_node()
    graph.add_physical_edge(node_index1, node_index2)
    graph.remove_physical_node(node_index1)
    assert node_index1 not in graph.physical_nodes
    assert node_index2 in graph.physical_nodes
    assert graph.num_physical_nodes == 1
    assert graph.num_physical_edges == 0


def test_remove_physical_node_from_3_nodes_graph(graph: GraphState) -> None:
    """Test removing a physical node from the graph with 3 nodes and edges."""
    node_index1 = graph.add_physical_node()
    node_index2 = graph.add_physical_node()
    node_index3 = graph.add_physical_node()
    graph.add_physical_edge(node_index1, node_index2)
    graph.add_physical_edge(node_index2, node_index3)
    q_index = graph.set_input(node_index1)
    graph.set_output(node_index3, q_index)
    graph.remove_physical_node(node_index2)
    assert graph.physical_nodes == {node_index1, node_index3}
    assert graph.num_physical_nodes == 2
    assert graph.num_physical_edges == 0
    assert graph.input_node_indices == {node_index1: q_index}
    assert graph.output_node_indices == {node_index3: q_index}


def test_remove_physical_edge_with_nonexistent_nodes(graph: GraphState) -> None:
    """Test removing an edge with nonexistent nodes from the graph."""
    with pytest.raises(ValueError, match="Node does not exist"):
        graph.remove_physical_edge(1, 2)


def test_remove_physical_edge_with_nonexistent_edge(graph: GraphState) -> None:
    """Test removing a nonexistent edge from the graph."""
    node_index1 = graph.add_physical_node()
    node_index2 = graph.add_physical_node()
    with pytest.raises(ValueError, match="Edge does not exist"):
        graph.remove_physical_edge(node_index1, node_index2)


def test_remove_physical_edge(graph: GraphState) -> None:
    """Test removing a physical edge from the graph."""
    node_index1 = graph.add_physical_node()
    node_index2 = graph.add_physical_node()
    graph.add_physical_edge(node_index1, node_index2)
    graph.remove_physical_edge(node_index1, node_index2)
    assert (node_index1, node_index2) not in graph.physical_edges
    assert (node_index2, node_index1) not in graph.physical_edges
    assert graph.num_physical_edges == 0


def test_set_output_raises_1(graph: GraphState) -> None:
    with pytest.raises(ValueError, match="Node does not exist node=1"):
        graph.set_output(1, 0)


def test_set_output_raises_2(graph: GraphState) -> None:
    node_index = graph.add_physical_node()
    graph.set_meas_basis(node_index, PlannerMeasBasis(Plane.XY, 0.5 * np.pi))
    with pytest.raises(ValueError, match=r"Cannot set output node with measurement basis."):
        graph.set_output(node_index, 0)


def test_set_meas_basis(graph: GraphState) -> None:
    """Test setting the measurement basis of a physical node."""
    node_index = graph.add_physical_node()
    meas_basis = PlannerMeasBasis(Plane.XZ, 0.5 * np.pi)
    graph.set_meas_basis(node_index, meas_basis)
    assert graph.meas_bases[node_index].plane == Plane.XZ
    assert graph.meas_bases[node_index].angle == 0.5 * np.pi


def test_check_meas_raises_value_error(graph: GraphState) -> None:
    """Test if measurement planes and angles are set improperly."""
    node_index = graph.add_physical_node()
    with pytest.raises(ValueError, match=f"Measurement basis not set for node {node_index}"):
        graph.check_meas_basis()


def test_check_meas_basis_success(graph: GraphState) -> None:
    """Test if measurement planes and angles are set properly."""
    graph.check_meas_basis()
    node_index1 = graph.add_physical_node()
    q_index = graph.set_input(node_index1)
    meas_basis = PlannerMeasBasis(Plane.XY, 0.5 * np.pi)
    graph.set_meas_basis(node_index1, meas_basis)
    graph.check_meas_basis()

    node_index2 = graph.add_physical_node()
    graph.add_physical_edge(node_index1, node_index2)
    graph.set_output(node_index2, q_index)
    graph.check_meas_basis()


def test_bipartite_edges(graph: GraphState) -> None:
    """Test the function that generate complete bipartite edges"""
    assert bipartite_edges(set(), set()) == set()
    assert bipartite_edges({1, 2, 3}, {1, 2, 3}) == {(1, 2), (1, 3), (2, 3)}
    assert bipartite_edges({1, 2}, {3, 4}) == {(1, 3), (1, 4), (2, 3), (2, 4)}
    graph.check_meas_basis()


if __name__ == "__main__":
    pytest.main()
