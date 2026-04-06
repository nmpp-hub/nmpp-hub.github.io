---
title: Finite Element Methods
---

## Group Leader

<p><strong><a href="/members/martin-campos-pinto/">Priv. Doz. Dr. Martin Campos Pinto</a></strong></p>

## Overview

The Finite Element group studies numerical models with enhanced stability and structure-preservation properties, with a particular focus on problems arising in electromagnetism and plasma physics.

Due to the presence of multiple scales and nonlinear interactions, the numerical simulation of plasmas often leads to computational problems of huge complexity. Numerical methods thus need to be computationally efficient, accurate and stable on very long time scales. As regards finite elements and more generally space discretization methods, it has been recognized since a few decades that long-time approximation and stability properties, as well as conservation of key physical invariants, are closely related with the preservation at the discrete level of algebraic functional structures such as De Rham sequences and Helmholtz decompositions. In this framework, the inherent stability of the discretization spaces can then be expressed by means of projection operators that provide a commuting diagram structure to the continuous and discrete de Rham sequences.

Over the years several structure-preserving methods have been developed along these lines, including the historical edge and face elements, and they have lead to very successful discretizations of a variety of problems such as Maxwell's equations. In particular, finite element methods that possess a stable commuting de Rham diagram are known to be accurate even for low-regularity electromagnetic fields, free of spurious eigenmodes and stable on very long time ranges. They are also naturally consistent with the divergence Gauss constraints on the fields.

In the group we study several extension of these methods for applications in Hamiltonian plasma models and coupling with discrete particle schemes on general geometries.

### Structure-preserving coupling with kinetic models

Recent research has shown that structure-preserving finite elements relying on commuting projection operators offer a canonical approach to variational discretizations of nonlinear kinetic problems such as Vlasov-Maxwell's equations, that preserve the Hamiltonian structure of the continuous models at the discrete level. One direction of study is develop a unified analysis of such methods and for specific problems, develop new discretization methods that allow for an efficient coupling with kinetic and hybrid models.

Research on this topic is carried out in collaboration with the [Kinetic](/groups/kinetic-gyrokinetic-models/) and the [Geometric](/groups/geometric-numerical-integration/) groups.

### High-order mass lumping on general geometries

In order to improve the efficiency and locality of the numerical schemes, several methods are being studied in the group. One is based on a new structure-preserving discretization that involve fully discontinuous finite element spaces. This framework has resulted in a new class of schemes called Conga for conforming/nonconforming Galerkin, which have block-diagonal mass matrices and provide a discretization of the Maxwell equations that is both energy conserving and spectrally correct, as opposed to standard Discontinuous Galerkin approximations.

Research on this topic is carried out in collaboration with the [MHD](/groups/magnetohydrodynamics/) group.

### Psydac: a Finite Element library

Psydac is a high-level finite-element library in Python 3, that uses high-order splines, mapped domains and MPI parallelization. In order to use Psydac, the user provides a geometry analytically or through an input file, and then defines the model equations in symbolic form (weak formulation) using Sympde, which provides the mathematical expressions and checks the semantic validity of the model. Once a finite element discretization has been chosen, Psydac maps the abstract concepts to concrete objects, the basic building blocks being MPI-distributed vectors and matrices. For all the computationally intensive operations (matrix and vector assembly, matrix-vector products, etc.), Psydac generates ad-hoc Python code which is accelerated using either Numba or Pyccel.

Research on this topic is carried out in collaboration with the [MHD](/groups/magnetohydrodynamics/) group.

## Additional Links

- [FEM official webpage](https://www.ipp.mpg.de/5150531/fem)
