from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from graphix_zx.common import Plane

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
    global_phase = np.angle(u[0, 0])
    u *= np.exp(-1j * global_phase)

    alpha = np.angle(u[1, 0]) + np.angle(u[0, 0])
    beta = 2 * np.arccos(np.abs(u[0, 0]))
    gamma = np.angle(u[0, 1]) - np.angle(u[1, 1])

    return alpha, beta, gamma


# TODO: there is room to improve the data type for angles
class LocalUnitary:
    alpha: float
    beta: float
    gamma: float

    def __init__(self, alpha: float = 0, beta: float = 0, gamma: float = 0) -> None:
        """Initialize the Euler angles.

        U -> Rz(alpha)Rx(beta)Rz(gamma)

        Parameters
        ----------
        alpha : float, optional
            angle for the first Rz, by default 0
        beta : float, optional
            angle for the Rx, by default 0
        gamma : float, optional
            angle for the last Rz, by default 0
        """
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
        return np.asarray(
            [
                [
                    np.cos(self.beta / 2) * np.exp(-1j * (self.alpha + self.gamma) / 2),
                    -1j * np.sin(self.beta / 2) * np.exp(-1j * (self.alpha - self.gamma) / 2),
                ],
                [
                    -1j * np.sin(self.beta / 2) * np.exp(1j * (self.alpha - self.gamma) / 2),
                    np.cos(self.beta / 2) * np.exp(1j * (self.alpha + self.gamma) / 2),
                ],
            ]
        )


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
    return bool(np.isclose(angle % (np.pi / 2), 0, atol=atol))


class LocalClifford(LocalUnitary):
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


class MeasBasis:
    plane: Plane
    angle: float

    def __init__(self, plane: Plane, angle: float) -> None:
        self.plane = plane
        self.angle = angle

    def get_vector(self) -> NDArray:
        return get_basis(self.plane, self.angle)


def get_basis(plane: Plane, angle: float) -> NDArray[np.complex128]:
    """Return the basis vector corresponding to the plane and angle.

    Parameters
    ----------
    plane : Plane
        measurement plane
    angle : float
        measurement angle

    Returns
    -------
    NDArray
        basis vector
    """
    if plane == Plane.XY:
        basis = np.asarray([1, np.exp(1j * angle)]) / np.sqrt(2)
    elif plane == Plane.YZ:
        basis = np.asarray([np.cos(angle / 2), 1j * np.sin(angle / 2)])
    elif plane == Plane.ZX:
        basis = np.asarray([np.cos(angle / 2), np.sin(angle / 2)])
    else:
        msg = "The plane must be one of XY, YZ, ZX"
        raise ValueError(msg)
    return basis


def _get_bloch_sphere_coordinates(vector: NDArray) -> tuple[float, float]:
    """Return the Bloch sphere coordinates corresponding to a vector.

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
    theta = 2 * np.arccos(np.abs(vector[0]))
    phi = np.angle(vector[1]) - np.angle(vector[0])
    return theta, phi


def get_basis_meas_info(vector: NDArray) -> tuple[Plane, float]:
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
    theta, phi = _get_bloch_sphere_coordinates(vector)
    if is_clifford_angle(phi):
        # YZ or ZX plane
        if is_clifford_angle(phi / 2):
            return Plane.ZX, theta + np.pi * (((phi / np.pi) % 2) - 1 / 2)
        return Plane.YZ, theta + np.pi * ((phi / np.pi) % 2)
    if is_clifford_angle(theta) and not is_clifford_angle(theta / 2):
        # XY plane
        return Plane.XY, phi + np.pi * (((theta / np.pi) % 2) - 1 / 2)
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
    plane, angle = get_basis_meas_info(vector)
    return MeasBasis(plane, angle)
