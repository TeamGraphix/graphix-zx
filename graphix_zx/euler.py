"""Euler angles and related functions.

This module provides:
- euler_decomposition: Decompose a 2x2 unitary matrix into Euler angles.
- get_bloch_sphere_coordinates: Get the Bloch sphere coordinates corresponding to a vector.
- is_clifford_angle: Check if an angle is a Clifford angle.
- LocalUnitary: Class to represent a local unitary.
- LocalClifford: Class to represent a local Clifford.
- update_lc_lc: Update a LocalClifford object with another LocalClifford object.
- update_lc_basis: Update a LocalClifford object with a MeasBasis object.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from graphix_zx.common import MeasBasis, Plane

if TYPE_CHECKING:
    from numpy.typing import NDArray


def euler_decomposition(u: NDArray) -> tuple[float, float, float]:
    """Decompose a 2x2 unitary matrix into Euler angles.

    U -> Rz(alpha)Rx(beta)Rz(gamma)

    Parameters
    ----------
    u : NDArray
        unitary 2x2 matrix

    Returns
    -------
    tuple[float, float, float]
        euler angles (alpha, beta, gamma)
    """
    global_phase = np.sqrt(np.linalg.det(u))
    u /= global_phase

    if np.isclose(u[0, 1], 0):
        alpha = 2 * np.angle(u[0, 0])
        beta = 0.0
        gamma = 0.0
    elif np.isclose(u[0, 0], 0):
        alpha = 2 * np.angle(u[1, 0] / (-1j))
        beta = np.pi
        gamma = 0.0
    else:
        alpha_p_gamma = np.angle(u[0, 0] / u[1, 1])
        alpha_m_gamma = np.angle(u[0, 1] / u[1, 0])

        alpha = (alpha_p_gamma + alpha_m_gamma) / 2
        gamma = (alpha_p_gamma - alpha_m_gamma) / 2

        cos_term = np.real(u[0, 0] / np.exp(1j * alpha_p_gamma / 2))
        sin_term = np.real(u[0, 1] / (-1j * np.exp(1j * alpha_m_gamma / 2)))

        beta = 2 * np.angle(cos_term + 1j * sin_term)

    return alpha, beta, gamma


def get_bloch_sphere_coordinates(vector: NDArray) -> tuple[float, float]:
    """Get the Bloch sphere coordinates corresponding to a vector.

    |psi> = cos(theta/2)|0> + exp(i*phi)sin(theta/2)|1>

    Parameters
    ----------
    vector : NDArray
        1 qubit state vector

    Returns
    -------
    tuple[float, float]
        Bloch sphere coordinates (theta, phi)
    """
    # normalize
    vector /= np.linalg.norm(vector)
    if np.isclose(vector[0], 0):
        theta = np.pi
        phi = np.angle(vector[1])
    else:
        global_phase = np.angle(vector[0])
        vector /= np.exp(1j * global_phase)
        phi = 0 if np.isclose(vector[1], 0) else np.angle(vector[1])
        cos_term = np.real(vector[0])
        sin_term = np.real(vector[1] / np.exp(1j * phi))
        theta = 2 * np.angle(cos_term + 1j * sin_term)
    return theta, phi


def _is_close_angle(angle: float, target: float, atol: float = 1e-9) -> bool:
    """Check if an angle is close to a target angle.

    Parameters
    ----------
    angle : float
        angle to check
    target : float
        target angle
    atol : float, optional
        absolute tolerance, by default 1e-9

    Returns
    -------
    bool
        True if the angle is close to the target angle
    """
    diff_angle = (angle - target) % (2 * np.pi)

    if diff_angle > np.pi:
        diff_angle = 2 * np.pi - diff_angle
    return bool(np.isclose(diff_angle, 0, atol=atol))


def is_clifford_angle(angle: float, atol: float = 1e-9) -> bool:
    """Check if an angle is a Clifford angle.

    Parameters
    ----------
    angle : float
        angle to check
    atol : float, optional
        absolute tolerance, by default 1e-9

    Returns
    -------
    bool
        True if the angle is a Clifford angle
    """
    return bool(_is_close_angle(angle % (np.pi / 2), 0, atol=atol))


# TODO: there is room to improve the data type for angles
class LocalUnitary:
    """Class to represent a local unitary.

    U -> Rz(alpha)Rx(beta)Rz(gamma)

    Attributes
    ----------
    alpha : float
        angle for the first Rz, by default 0
    beta : float
        angle for the Rx, by default 0
    gamma : float
        angle for the last Rz, by default 0
    """

    alpha: float
    beta: float
    gamma: float

    def __init__(self, alpha: float = 0, beta: float = 0, gamma: float = 0) -> None:
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma

    def print_angles(self) -> None:
        """Print the Euler angles."""
        print(f"alpha: {self.alpha}, beta: {self.beta}, gamma: {self.gamma}")  # noqa: T201

    def get_matrix(self) -> NDArray:
        """Return the 2x2 unitary matrix corresponding to the Euler angles.

        Returns
        -------
        NDArray
            2x2 unitary matrix
        """
        return _rz(self.alpha) @ _rx(self.beta) @ _rz(self.gamma)


class LocalClifford(LocalUnitary):
    """Class to represent a local Clifford.

    U -> Rz(alpha)Rx(beta)Rz(gamma)
    Each angle must be a multiple of pi/2.

    Attributes
    ----------
    alpha : float
        angle for the first Rz, by default 0
    beta : float
        angle for the Rx, by default 0
    gamma : float
        angle for the last Rz, by default 0
    """

    alpha: float
    beta: float
    gamma: float

    def __init__(self, alpha: float = 0, beta: float = 0, gamma: float = 0) -> None:
        """Initialize the Euler angles for Clifford gates.

        Parameters
        ----------
        alpha : float, optional
            angle for the first Rz. The angle must be a multiple of pi/2, by default 0
        beta : float, optional
            angle for the Rx. The angle must be a multiple of pi/2, by default 0
        gamma : float, optional
            angle for the last Rz. The angle must be a multiple of pi/2, by default 0
        """
        self._angle_check(alpha, beta, gamma)
        super().__init__(alpha, beta, gamma)

    @classmethod
    def _angle_check(cls, alpha: float, beta: float, gamma: float, atol: float = 1e-9) -> None:
        """Check if the angles are Clifford angles.

        Parameters
        ----------
        alpha : float
            angle for the first Rz
        beta : float
            angle for the Rx
        gamma : float
            angle for the last Rz
        atol : float, optional
            absolute tolerance, by default 1e-9

        Raises
        ------
        ValueError
            if any of the angles is not a Clifford angle
        """
        if not any(is_clifford_angle(angle, atol=atol) for angle in [alpha, beta, gamma]):
            msg = "The angles must be multiples of pi/2"
            raise ValueError(msg)


def _get_meas_basis_info(vector: NDArray) -> tuple[Plane, float]:
    """Return the measurement plane and angle corresponding to a vector.

    Parameters
    ----------
    vector : NDArray
        1 qubit state vector

    Returns
    -------
    tuple[Plane, float]
        measurement plane and angle

    Raises
    ------
    ValueError
        if the vector does not lie on any of 3 planes
    """
    theta, phi = get_bloch_sphere_coordinates(vector)
    if is_clifford_angle(phi):
        # YZ or ZX plane
        if is_clifford_angle(phi / 2):  # 0 or pi
            if _is_close_angle(phi, np.pi):
                theta = -theta
            return Plane.ZX, theta
        if _is_close_angle(phi, 3 * np.pi / 2):
            theta = -theta
        return Plane.YZ, theta
    if is_clifford_angle(theta) and not is_clifford_angle(theta / 2):
        # XY plane
        if _is_close_angle(theta, 3 * np.pi / 2):
            phi += np.pi
        return Plane.XY, phi
    msg = "The vector does not lie on any of 3 planes"
    raise ValueError(msg)


def update_lc_lc(lc1: LocalClifford, lc2: LocalClifford) -> LocalClifford:
    """Update a LocalClifford object with another LocalClifford object.

    Parameters
    ----------
    lc1 : LocalClifford
        left LocalClifford
    lc2 : LocalClifford
        right LocalClifford

    Returns
    -------
    LocalClifford
        multiplied LocalClifford
    """
    matrix1 = lc1.get_matrix()
    matrix2 = lc2.get_matrix()

    matrix = matrix1 @ matrix2
    alpha, beta, gamma = euler_decomposition(matrix)
    return LocalClifford(alpha, beta, gamma)


def update_lc_basis(lc: LocalClifford, basis: MeasBasis) -> MeasBasis:
    """Update a LocalClifford object with a MeasBasis object.

    Parameters
    ----------
    lc : LocalClifford
        LocalClifford
    basis : MeasBasis
        MeasBasis

    Returns
    -------
    MeasBasis
        updated MeasBasis
    """
    matrix = lc.get_matrix()
    vector = basis.get_vector()

    vector = matrix @ vector
    plane, angle = _get_meas_basis_info(vector)
    return MeasBasis(plane, angle)


def _rx(angle: float) -> NDArray[np.complex128]:
    return np.asarray(
        [
            [np.cos(angle / 2), -1j * np.sin(angle / 2)],
            [-1j * np.sin(angle / 2), np.cos(angle / 2)],
        ]
    )


def _rz(angle: float) -> NDArray[np.complex128]:
    return np.asarray(
        [
            [np.exp(1j * angle / 2), 0],
            [0, np.exp(-1j * angle / 2)],
        ]
    )
