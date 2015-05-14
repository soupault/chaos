############################################################
# This file contains all functions for two modes system
#
# First, please complete function velocity(), velocity_reduced(),
# velocity_phase(), stabilityMatrix_reduced(), groupTransform()
# and reduceSymmetry(), and set case = 1 to validate your code
#
# Next, complete case2, and case3.
############################################################
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from numpy.random import rand
from scipy.integrate import odeint
from scipy.optimize import fsolve

# Coefficients
G_mu1 = -2.8
G_c1 = -7.75
G_a2 = -2.66

# Chosen template
group_generator = np.array([[0, -1, 0, 0],
                            [1, 0, 0, 0],
                            [0, 0, 0, -2],
                            [0, 0, 2, 0]])
template_point = np.array([1, 0, 0, 0])
group_tangent = np.dot(group_generator, template_point)


def velocity(stateVec, t):      
    """
    velocity in the full state space.
    
    stateVec: state vector [x1, y1, x2, y2]
    t: just for convention of odeint, not used.
    return: velocity at stateVec. Dimension [1 x 4]
    """
    x1 = stateVec[0]
    y1 = stateVec[1]
    x2 = stateVec[2]
    y2 = stateVec[3]
    r2 = x1**2 + y1**2
    
    velo = np.array([(G_mu1 - r2) * x1 + G_c1 * (x1 * x2 + y1 * y2),
                     (G_mu1 - r2) * y1 + G_c1 * (x1 * y2 - x2 * y1),
                     x2 + y2 + x1 ** 2 - y1 ** 2 + G_a2 * x2 * r2,
                     -x2 + y2 + 2 * x1 * y1 + G_a2 * y2 * r2])
    return velo


def velocity_reduced(state_reduced, t):
    """
    velocity in the slice after reducing the continous symmetry

    state_reduced: state vector in slice [\hat{x}_1, \hat{x}_2, \hat{y}_2]
    t: not used
    return: velocity at stateVect_reduced. dimension [1 x 3]
    """
    state_red_full = (state_reduced[0], 0, state_reduced[1],
                     state_reduced[2])
    velocity_at_state = velocity(state_red_full, 1)
    tangent_at_state = np.dot(group_generator, state_red_full)

    velo = velocity_at_state - np.inner(velocity_phase(state_reduced),
                                        tangent_at_state)
    velo = np.array([velo[0], velo[2], velo[3]])
    return velo


def velocity_phase(state_reduced):
    """
    phase velocity. 

    stateVec_reduced: state vector in slice [\hat{x}_1, \hat{x}_2, \hat{y}_2]
    Note: phase velocity only depends on the state vector
    """
    state_red_full = (state_reduced[0], 0, state_reduced[1], state_reduced[2])
    velocity_at_state = velocity(state_red_full, 1)
    tangent_at_state = np.dot(group_generator, state_red_full)

    velo_phase = np.dot(velocity_at_state.T, group_tangent) /\
                 np.inner(tangent_at_state.T, group_tangent)

    return velo_phase


def integrator(init_state, dt, nstp):
    """
    integrate two modes system in the full state space.

    init_state: initial state [x1, y1, x2, y2]
    dt: time step 
    nstp: number of time step
    """
    states = odeint(velocity, init_state, np.arange(0, dt*nstp, dt))
    return states


def integrator_reduced(init_state, dt, nstp):    
    """
    integrate two modes system in the slice

    init_state: initial state [\hat{x}_1, \hat{x}_2, \hat{y}_2]
    dt: time step 
    nstp: number of time step
    """
    states = odeint(velocity_reduced, init_state, np.arange(0, dt*nstp, dt))
    return states


def stabilityMatrix(state):
    """
    calculate the stability matrix in the full state space

    state: state vector in slice [\hat{x}_1, \hat{x}_2, \hat{y}_2]
    return: stability matrix. Dimension [3 x 3]
    """
    x1, y1, x2, y2 = state

    stab = np.array([[G_mu1-3*x1**2+G_c1*x2-y1**2, G_c1*y2-2*x1*y1,
                      G_c1*x1, G_c1*y1],
                     [G_c1*y2-2*x1*y1, G_mu1-x1**2-G_c1*x1-3*y1**2,
                      -G_c1*y1, G_c1*x1],
                     [2*x1+2*G_a2*x1*x2, 2*G_a2*x2*y1-2*y1,
                      1+G_a2*(x1**2+y1**2), 1],
                     [2*y1+2*G_a2*x1*y2, 2*x1+2*G_a2*y1*y2,
                      -1, 1+G_a2*(x1**2+y1**2)]])
    return stab


def stabilityMatrix_reduced(state_reduced):
    """
    calculate the stability matrix on the slice

    stateVec_reduced: state vector in slice [\hat{x}_1, \hat{x}_2, \hat{y}_2]
    return: stability matrix. Dimension [3 x 3]
    """
    x1 = state_reduced[0]
    y1 = 0
    x2 = state_reduced[1]
    y2 = state_reduced[2]
    state_ext = (x1, y1, x2, y2)

    stab_full = stabilityMatrix(state_ext)
    tangent_at_state = np.dot(group_generator, state_ext)

    sqr_braket = np.dot(np.inner(tangent_at_state, group_tangent),
                        stab_full.T) - \
                 np.dot(np.inner(velocity(state_ext, 0), group_tangent),
                        group_generator.T)

    stab = np.zeros_like(stab_full)
    for i in range(4):
        for j in range(4):
            stab[i, j] = stab_full[i, j] - \
                         np.dot(tangent_at_state[i],
                                np.dot(sqr_braket, group_tangent)[j]) / \
                         np.inner(tangent_at_state, group_tangent) ** 2 - \
                         np.inner(velocity(state_ext, 0), group_tangent) / \
                         np.inner(tangent_at_state, group_tangent) * \
                         group_generator[i, j]

    stab = np.delete(stab, 1, axis=0)
    stab = np.delete(stab, 1, axis=1)
    return stab


def groupTransform(state, phi):
    """
    perform group transform on a particular state. Symmetry group is 'g(phi)'
    and state is 'x'. the transformed state is ' xp = g(phi) * x '
 
    state: state in the full state space. Dimension [1 x 4]
    phi: group angle. in range [0, 2*pi]
    return: the transformed state. Dimension [1 x 4]
    """
    g = np.array([
        [np.cos(phi), -np.sin(phi), 0, 0],
        [np.sin(phi), np.cos(phi), 0, 0],
        [0, 0, np.cos(2*phi), -np.sin(2*phi)],
        [0, 0, np.sin(2*phi), np.cos(2*phi)]
    ])
    state_transformed = np.transpose(np.dot(g, np.transpose(state)))
    return state_transformed


def reduceSymmetry(states):
    """
    tranform states in the full state space into the slice.
    Hint: use numpy.arctan2(y,x)
    Note: this function should be able to reduce the symmetry
    of a single state and that of a sequence of states. 

    states: states in the full state space. dimension [m x 4] 
    return: the corresponding states on the slice dimension [m x 3]
    """
    if states.ndim == 1: # if the state is one point
        x1, y1 = states[:2]
        if x1 == 0:
            phi = np.arccos(0)
        else:
            phi = np.arctan2(-y1, x1)
        x1s, _, x2s, y2s = groupTransform(states, phi)
        reduced_states = (x1s, x2s, y2s)

    elif states.ndim == 2: # if they are a sequence of state points
        reduced_states = np.zeros((states.shape[0], states.shape[1]-1))
        for i in range(states.shape[0]):

            x1, y1 = states[i, :2]
            if x1 == 0:
                phi = np.arccos(0)
            else:
                phi = np.arctan2(-y1, x1)
            x1s, _, x2s, y2s = groupTransform(states[i, :], phi)
            reduced_states[i, 0] = x1s
            reduced_states[i, 1] = x2s
            reduced_states[i, 2] = y2s

    else:
        reduced_states = (None, None, None)

    return reduced_states


def plotFig(orbit):
    fig = plt.figure(figsize=(8,6))
    ax = fig.add_subplot(111, projection='3d')
    ax.plot(orbit[:, 0], orbit[:, 1], orbit[:, 2])
    ax.set_xlabel("X Axis")
    ax.set_ylabel("Y Axis")
    ax.set_zlabel("Z Axis")


if __name__ == '__main__':
    case = 3

    if case == 1:
        """
        validate your implementation.
        We generate an ergodic trajectory, and then use two
        different methods to obtain the corresponding trajectory in slice.
        The first method is post-processing. The second method utilizes
        the dynamics in the slice directly.
        """
        x0 = 0.1 * rand(4)  # random inital state
        x0_reduced = reduceSymmetry(x0)  # initial state transformed into slice
        dt = 0.005
        nstp = 500.0 / dt
        # trajectory in the full state space
        orbit = integrator(x0, dt, nstp)
        # trajectory in the slice by reducing the symmety
        reduced_orbit = reduceSymmetry(orbit)
        # trajectory in the slice by integration in slice
        reduced_orbit2 = integrator_reduced(x0_reduced, dt, nstp)
        
        plotFig(orbit[:, 0:3])
        plotFig(reduced_orbit[:, 0:3])
        plotFig(reduced_orbit2[:, 0:3])
        plt.show()

        print(stabilityMatrix_reduced(np.array([0.1, 0.2, 0.3])))

    elif case == 2:
        """
        Try reasonable guess to find relative equilibria.
        One possible way: numpy.fsolve
        """
        guess = np.array([0.5, -0.5, 0.1])  # a relative good guess

        req = fsolve(velocity_reduced, guess, args=0)
        print('Relative equilibrium: ', req)
        print('Phase velocity at equilibrium: ', velocity_phase(req))

        # see how relative equilibrium drifts in the full state space
        req_full = np.array([req[0], 0, req[1], req[2]])
        dt = 0.005
        T = np.abs(2 * np.pi / velocity_phase(req))
        nstp = np.round(T / dt)
        orbit = integrator(req_full, dt, nstp)
        plotFig(orbit[:, 0:3])
        plt.show()

    elif case == 3:
        """
        return map in the Poincare section. This case is similar to hw3.

        We start with the relative equilibrium, and construct a Poincare
        section by its real and imaginary part of its expanding
        eigenvector (real part and z-axis is in the Poincare section).

        Then we record the Poincare intersection points by an ergodic
        trajectory. Sort them by their distance to the relative equilibrium,
        and calculate the arc length r_n from the reltative equilibrium to
        each of them. After that we construct map r_n -> r_{n+1},
        r_n -> r_{n+2}, r_n -> r_{n+3}, etc. The fixed points of these map
        give us good initial guesses for periodic orbits. If you like, you
        can use Newton method to refine these initial conditions. For HW5,
        you are only required to obtain the return map.
        """
        # copy the relative equilibrium from case 2 here ([rx1, rx2, ry2])
        req = np.array([0.43996558, -0.38626706, 0.0702044])
        # find the real part and imaginary part of the expanding eigenvector at req
        # You should get: Vi = array([-0.        ,  0.58062392, -0.00172256])
        stability_req = stabilityMatrix_reduced(req)
        w, v = np.linalg.eig(stability_req)
        # print('numbers', w)
        # print('vectors', v)
        Vr = np.array([e.real for e in v[:, 1]])
        Vi = np.array([e.imag for e in v[:, 1]])

        # For simplicity, we choose to work in a new coordiates, whose origin
        # is the relative equilibrium.
        # Construct an orthogonal basis from Vr, Vi and z-axis (\hat{y}_2 axis).
        # Hint: numpy.qr()
        # You should get
        # Py = array([-0.12715969, -0.9918583 ,  0.00689345]) : normalized
        # q, r = np.linalg.qr(np.vstack((Vr, Vi, np.array([0.1, 0.1, 0.1]))))
        # print(q)
        # print(r)
        # Px = Vr / np.linalg.norm(Vr) # should be in the same direction of Vr
        # Px = q[:, 0]
        # Py = q[:, 1]
        # print(Px, Py)
        # Py =  # should be in the plan spanned by (Vr, Vi), and orthogonal to Px
        # Pz =  # should be orthogonal to Px and Py

        # # produce an ergodic trajectory started from relative equilbirum
        # x0_reduced = req + 0.0001*Vr
        # dt = 0.005
        # nstp = 800.0 / dt
        # orbit = integrator_reduced(x0_reduced, dt, nstp);
        # # project this orbit to the new basis [Px, Py, Pz],
        # # also make the relative equilibrium be the origin.
        # # To check your answer, you can set 'orbit = req' on purpose and see
        # # whether orbit_prj is (0, 0, 0), also set 'oribt = Px + req' and see
        # # whether orbit_prj is (1, 0, 0)
        # orbit_prj =
        #
        # # Choose Poincare section be Px = 0 (y-z plane), find all the intersection
        # # points by orbit_prj.
        # # Note: choose the right direction of this Poincare section, otherwise,
        # # you will get two branches of intersection points.
        # # Hint: you can find adjacent points who are at the opposite region of this
        # # poincare section and then use simple linear interpolation to get the
        # # intersection point.
        #
        # PoincarePoints = # the set of recored Poincare intersection points
        # Pnum =  # number of intersection points
        # distance = # the Euclidean distance of intersection points to the orgin
        #            # Please distinguish Euclidean distance with the arch length that follows.
        #            # Euclidean distance of a Poincare intersection point P_i = (0, yi, zi)
        #            # (the x coordinate is zero since section is chosen as Px = 0)
        #            # is just \sqrt{yi^2 + zi^2}
        #
        #
        #
        #
        # # Now reorder the distance from small to large. Also keep note which distance correspond
        # # to which intersection point. Let us calculate the curvilinear length (arch length) along the
        # # intersection curve.
        # # Suppose the Euclidean distance is [d1, d2,..., dm] (sorted from small to large),
        # # the corresponding intersection points are
        # # [p_{k_1}, p_{k_2}, ..., p_{k_m}], then the arch length of p_{k_i} from relative equilibrium is
        # # r_{k_i} = \sum_{j = 1}^{j = i} \sqrt( (p_{k_j} - p_{k_{j-1}})^2 )
        # # here p_{k_0} refers to the relative equilibrium itself, which is the origin.
        # # Example: r_{k_2} = |p_{k_2} - p_{k_1}| + |p_{k_1} - p_{k_0}|
        # # Basically, we are summing the length segment by segment.
        # # In this way, we have the arch length of each Poincare intersection point. The return map
        # # r_n -> r_{n+1} indicates how intersection points stretch and fold on the Poincare section.
        #
        # length = # arch length
        #
        # # plot the return map with diffrent order. Try to locate the fixed
        # # points in each of these return map. Each of them corresponds to
        # # the initial condtion of a periodic orbit. Use the same skill in HW3 to
        # # get the inital conditions for these fixed points, and have a look at the
        # # structure of the corresponding periodic orbits. This model may be analized
        # # further when we try to understand symbolic dynamics in future.
        # # Have fun !
        #
        # # plot r_n -> r_{n+1} # 1st order
        # # plot r_n -> r_{n+2} # 2nd order
        # # plot r_n -> r_{n+3} # 3nd order
        # # plot r_n -> r_{n+4} # 4th order
