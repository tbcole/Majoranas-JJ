import majoranaJJ.operators.sparse_operators as spop #sparse operators
import numpy as np
import scipy.linalg as LA
import scipy.sparse.linalg as spLA
from scipy.signal import argrelextrema
import sys
import matplotlib.pyplot as plt

#Assuming linear behavior of the E vs gamma energy dispersion
#Taking the slope and the initial points in the energy vs gamma plot
#Extrapolate to find zero energy crossing
def linear(
    coor, ax, ay, NN, mu,
    NNb = None, Wj = 0, cutx = 0, cuty = 0, V = 0,
    gammax = 0, gammay = 0, gammaz = 0,
    alpha = 0, delta = 0 , phi = 0,
    qx = 0, qy = 0, periodicX = True, periodicY = False,
    k = 20, sigma = 0, which = 'LM', tol = 0, maxiter = None
    ):

    #saving the particle energies, all energies above E=0
    Ei = spop.EBDG(
        coor, ax, ay, NN, NNb = NNb, Wj = Wj,
        cutx = cutx, cuty = cuty,
        V = V, mu = mu,
        gammax = gammax, gammay = gammay, gammaz = gammaz,
        alpha = alpha, delta = delta, phi = phi,
        qx = qx, qy = qy,
        periodicX = periodicX, periodicY = periodicY,
        k = k, sigma = sigma, which = which, tol = tol, maxiter = maxiter
        )[int(k/2):][::2]
    #print(Ei)

    deltaG = 0.00001
    gammanew = gammax + deltaG

    #saving the particle energies, all energies above E=0
    Ef = spop.EBDG(
        coor, ax, ay, NN, NNb = NNb, Wj = Wj,
        cutx = cutx, cuty = cuty,
        V = V, mu = mu,
        gammax = gammanew, gammay = gammay, gammaz = gammaz,
        alpha = alpha, delta = delta, phi = phi,
        qx = qx, qy = qy,
        periodicX = periodicX, periodicY = periodicY,
        k = k, sigma = sigma, which = which, tol = tol, maxiter = maxiter
        )[int(k/2):][::2]
    #print(Ef)

    m = np.array((Ef - Ei)/(gammanew - gammax)) #slope, linear dependence on gamma
    #print(m)
    b = np.array(Ei - m*gammax) #y-intercept
    G_crit = np.array(-b/m) #gamma value that E=0 for given mu value
    #print(G_crit)
    return G_crit

"""
This function calculates the phase transition points. To work it needs energy eigenvalues and eigenvectors of unperturbed Hamiltonian, or a Hamiltonian without any Zeeman field. When a Zeeman field is turned on, perturbation theory can be used to calculate the new energy eigenvalues and eigenvectors creating a reduced subspace of the initial Hilbert space. Works in units of gamme (meV)
"""
def lowE(
    coor, ax, ay, NN, mu, gi, gf,
    NNb = None, Wj = 0, cutx = 0, cuty = 0,
    V = 0, gammax = 0,  gammay = 0, gammaz = 0,
    alpha = 0, delta = 0, phi = 0,
    qx = 0, qy = None,
    Tesla = False, Zeeman_in_SC = True, SOC_in_SC = True,
    k = 20, tol = 0.001, n_bounds = 2
    ):

    Lx = (max(coor[:, 0]) - min(coor[:, 0]) + 1)*ax #Unit cell size in x-direction
    H0 = spop.HBDG(coor, ax, ay, NN, NNb=NNb, Wj=Wj, cutx=cutx, cuty=cuty, V=V, mu=mu, gammaz=1e-5, alpha=alpha, delta=delta, phi=phi, qx=1e-4*(np.pi/Lx), qy=qy, Tesla=Tesla, Zeeman_in_SC=Zeeman_in_SC, SOC_in_SC=SOC_in_SC) #gives low energy basis
    eigs_0, vecs_0 = spLA.eigsh(H0, k=k, sigma=0, which='LM')
    vecs_0_hc = np.conjugate(np.transpose(vecs_0)) #hermitian conjugate

    H_G0 = spop.HBDG(coor, ax, ay, NN, NNb=NNb, Wj=Wj, cutx=cutx, cuty=cuty, V=V, mu=mu, gammax=0, alpha=alpha, delta=delta, phi=phi, qx=qx, qy=qy, Tesla=Tesla, Zeeman_in_SC=Zeeman_in_SC, SOC_in_SC=SOC_in_SC) #Matrix that consists of everything in the Hamiltonian except for the Zeeman energy in the x-direction
    H_G1 = spop.HBDG(coor, ax, ay, NN, NNb=NNb, Wj=Wj, cutx=cutx, cuty=cuty, V=V, mu=mu, gammax=1, alpha=alpha, delta=delta, phi=phi, qx=qx, qy=qy, Tesla=Tesla, Zeeman_in_SC=Zeeman_in_SC, SOC_in_SC=SOC_in_SC) #Hamiltonian with ones on Zeeman energy along x-direction sites
    HG = H_G1 - H_G0 #the proporitonality matrix for gamma-x, it is ones along the sites that have a gamma value
    HG0_DB = np.dot(vecs_0_hc, H_G0.dot(vecs_0))
    HG_DB = np.dot(vecs_0_hc, HG.dot(vecs_0))

    G_crit = []
    delta_gam = abs(gf - gi)
    steps = int((delta_gam/(0.5*tol))) +1
    gx = np.linspace(gi, gf, steps)
    eig_arr = np.zeros((gx.shape[0]))
    for i in range(gx.shape[0]):
        H_DB = HG0_DB + gx[i]*HG_DB
        eigs_DB, U_DB = LA.eigh(H_DB)
        eig_arr[i] = eigs_DB[int(k/2)]

    #checking edge cases
    if eig_arr[0] < tol:
        G_crit.append(gx[0])
    if eig_arr[-1] < tol:
        G_crit.append(gx[-1])

    local_min_idx = np.array(argrelextrema(eig_arr, np.less)[0]) #local minima indices in the E vs gamma plot
    print(local_min_idx.size, "local minima found")
    plt.plot(gx, eig_arr, c='b')
    plt.scatter(gx[local_min_idx], eig_arr[local_min_idx], c='r', marker = 'X')
    plt.show()

    tol = tol/1000
    for i in range(0, local_min_idx.size): #eigs_min.size
        gx_c = gx[local_min_idx[i]] #gx[ZEC_idx[i]]""" #first approx g_critical
        print("Checking for ZEC around gamma = {}, energy = {}".format(gx_c, eig_arr[local_min_idx[i]]))
        gx_lower = gx[local_min_idx[i]-1]#gx[ZEC_idx[i]-1]""" #one step back
        gx_higher = gx[local_min_idx[i]+1]#gx[ZEC_idx[i]+1]""" #one step forward

        delta_gam = (gx_higher - gx_lower)
        n_steps = (int((delta_gam/(0.5*tol))) + 1)*100
        gx_finer = np.linspace(gx_lower, gx_higher, n_steps) #high res gamma around supposed zero energy crossing (local min)
        eig_arr_finer = np.zeros((gx_finer.size)) #new eigenvalue array
        for j in range(gx_finer.shape[0]):
            H_DB = HG0_DB + gx_finer[j]*HG_DB
            eigs_DB, U_DB = LA.eigh(H_DB)
            eig_arr_finer[j] = eigs_DB[int(k/2)] #k/2 -> lowest postive energy state

        min_idx_finer = np.array(argrelextrema(eig_arr_finer, np.less)[0]) #new local minima indices
        eigs_min_finer = eig_arr_finer[min_idx_finer] #isolating local minima
        for m in range(min_idx_finer.shape[0]):
            if eigs_min_finer[m] < tol:
                crossing_gamma = gx_finer[min_idx_finer[m]]
                G_crit.append(crossing_gamma)
                print("Crossing found at Gx = {} | E = {} meV".format(crossing_gamma, eigs_min_finer[m]))

                plt.plot(gx_finer, eig_arr_finer, c = 'b')
                plt.scatter(G_crit, eigs_min_finer[m], c= 'r', marker = 'X')
                plt.show()
    G_crit = np.array(G_crit)
    return G_crit
