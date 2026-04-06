---
title: Kinetic and Gyrokinetic Models
---

## Group Leader

<p><strong><a href="/members/stefan-possanner/">Dr. Stefan Possanner</a></strong></p>

## Overview

Kinetic theory gives a probabilistic description of the plasma in terms of a distribution function in phase-space. This description is more comprehensive than the magneto-hydrodynamic description but at the same time more computationally demanding. A major challenge for the numerical solution of the kinetic model is the rather high dimensionality of four to six dimensions depending on the geometry and the level of approximation. In addition, the requirements on the resolution are high, since small filaments and turbulent structures can occur in phase-space.

The kinetics group of the NMPP section works on the development and analysis of robust and efficient algorithms for numerical simulations of the kinetic equations, in its most general six-dimensional form as well as the gyrokinetics equations. Mostly particle-in-cell and semi-Lagrangian methods are developed, but Eulerian methods based on spectral discontinuous Galerkin are also under scrutiny. Moreover, the group works with the analysis of various approximations in the model and on verification.

### Geometric Particle-In-Cell Methods

The main focus of the group is currently the development of geometric particle-in-cell algorithms. Such particle-based codes are well-suited for high-dimensional problems and scale relatively well on supercomputers. In collaboration with the groups on “Geometrical numerical integration” and “Geometric finite elements”, we develop structure-preserving schemes for kinetic and hybrid models of various forms. Our methods do not only conserve the physical structure of the problem but also come with favorable numerical stability properties, in particular for long-time simulations. Our theoretical framework allows to mix various types of discretization methods. In particular a Fourier description of the angular dimensions can be combined with a polynomial finite element description of the radial component. At the moment we are interested in extending our methods to reduced models, such as a drift-kinetic description, and regarding the geometry. Together with physicists from Aalto University, it is our goal to simulate plasmas – in particular in the edge and scrape off layer – within the framework of an EUROfusion project.

### Interaction between plasma waves and energetic particles

Waves in plasmas are usually described as magneto-hydrodynamic fluids. However, there may be interaction with fast particles, that cause a growth or damping of these waves. We are currently developing structure-preserving schemes that combine a magneto-hydrodynamical description of the bulk of the plasma with a kinetic description of the fast particles. Our investigations focus on current and pressure coupling models of the full idealized MHD equations and their extension to two-fluid MHD. We collaborate with the MHD group on the stability analysis and a coupling to the equilibrium solver GVEC.

### Implementation on high-performance computers and efficiency

Since the solution of the kinetic equations is computationally very demanding, the group is also concerned with efficiency and scalability of the solution methods. During the past years, we have developed two highly optimized codes: The first code is based on the semi-Lagrangian method and has been implemented in collaboration with the Max Planck computing center MPCDF. The second one builds on discontinuous Galerkin methods and has been developed together with TU Munich as a part of the DFG project EXA-DG. The former is currently used by the group “Zonal flows in turbulent plasmas” to compare the kinetic and the gyrokinetic model.

On the other hand, certain problems can also be solved based on compressed methods – like low rank tensors or sparse grids – with high efficiency.

## Additional Links

- [KGKM official webpage](https://www.ipp.mpg.de/4104717/kgkm)
