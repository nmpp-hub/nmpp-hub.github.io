---
title: Zonal Flows in Turbulent Plasmas
---

## Group Leader

<p><strong>Priv. Doz. Dr. Klaus Hallatschek</strong></p>

<!-- CUSTOM:CONTENT:START -->
The group studies the zonal flows with massively parallel computer simulations of plasma and planetary turbulence, with the goal to make predictions of their long-term evolution and experimentally observed switching effects between different flow patterns.

## Zonal Flows in Jovian Atmospheres
Everybody has already observed how a flow — for example when pouring milk into a cup of coffee — decays turbulently into smaller and smaller vortices until it is completely consumed. A strikingly unfamiliar behaviour occurs on the giant gas planets Jupiter and Saturn, which are turbulent due to the temperature contrast between their hot interior and cold surface: instead of producing smaller and smaller eddies, the turbulence creates planet-spanning east and west flows. These "zonal flows" are very conspicuous on the planets from the dark and bright cloud bands that align with them along the lines of latitude.

## Zonal Flows in Magnetised Plasmas
Convective turbulence also exists in the torus shaped fusion reactors of the tokamak or stellarator type due to the enormous temperature gradients therein. Analogous to the case of the gas planets it also gives rise to global flows, this time along the small torus circumference. The flows can be detected by sampling the electric potential, which shows pronounced bands, each extending on a complete flux surface, similar to the Jovian cloud bands. The flows in turn exert a decisive damping effect on the turbulence, which is favourable for the plasma confinement and greatly reduces the technical effort necessary to keep the plasma burning.

## Massively Parallel Turbulence Simulations
The exploration of the zonal flows necessitates the simulation of the underlying turbulence to sufficient precision and for so long that it requires to employ massively parallel computers with thousands of cores and the corresponding specialised computer codes. For this purpose the group develops the non-local two-fluid code NLET for the plasma turbulence as well as the anelastic Cartesian code NAN for the planetary turbulence.

The long-term prediction of the evolution of the zonal flows would on one hand provide a safer basis for extrapolations of current fusion experiments to larger machines, such as Iter. On the other hand this might open a way to manipulate the flows to improve the confinement, which could reduce drastically the cost and complexity of nuclear fusion.

## 6D Tokamak Edge Turbulence Simulations
The most interesting part of zonal flow physics occurs at the vaccuum boundary of a confined plasma, the so called "edge". Empirically, crossing a certain threshold of the heat flux over the edge leads to a sudden transition to the “high confinement mode” (LH-transition), which sets the stage of the overall confinement level and is an indispensable effect for the functioning of all current and planned fusion experiments. The transition occurs simultaneously with a rapid spin-up of a strong poloidal flow in the edge, which is believed to be the cause of the transition. Despite decades of research, the edge region and particularly the exact cause of the LH-transition is theoretically still largely uncharted territory, since it is not possible to carry out physically accurate simulations of the turbulence there. Present approaches approximate the motion of the plasma particles (gyrokinetics, multifluid equations) to short-cut the computations, but break down in the edge due to the large fluctuation levels, comparable level of electric and magnetic forces on the ions, and the significance of collisions. We work towards lifting these restrictions. A promising approach is to solve the kinetic equation based on the full particle motion, which incurs higher computational cost, but on the other hand greatly simplifies the equations allowing more structured and optimised numerical procedures as implemented by the group "Kinetic and gyrokinetic models".

## Additional Links
- [Scientific Divisions](https://www.ipp.mpg.de/15333/bereiche)
- [Numerical Methods in Plasma Physics](https://www.ipp.mpg.de/ippcms/eng/for/bereiche/numerik)
<!-- CUSTOM:CONTENT:END -->

## Members

<!-- AUTO:MEMBERS:START -->
<ul>
  <li><a href="/members/klaus-hallatschek/">Klaus Hallatschek</a></li>
</ul>
<!-- AUTO:MEMBERS:END -->

## Publications

<!-- AUTO:PUBLICATIONS:START -->
<table>
  <thead>
    <tr>
      <th>Year</th>
      <th>Title</th>
      <th>Authors</th>
      <th>Venue</th>
      <th>Link</th>
    </tr>
  </thead>
  <tbody>
  <tr>
    <td>2025</td>
    <td>Convergence of Splitting Methods on Rotating Grids for the Magnetized Vlasov Equation</td>
    <td>Nils Schild, Mario Räth, <a href="/members/klaus-hallatschek/">Klaus Hallatschek</a>, Katharina Kormann</td>
    <td>SIAM Journal on Scientific Computing</td>
    <td><a href="https://doi.org/10.1137/24m1659327">DOI</a></td>
  </tr>
  <tr>
    <td>2024</td>
    <td>A performance portable implementation of the semi-Lagrangian algorithm in six dimensions</td>
    <td>Nils Schild, Mario Räth, Sebastian Eibl, <a href="/members/klaus-hallatschek/">Klaus Hallatschek</a>, Katharina Kormann</td>
    <td>Computer Physics Communications</td>
    <td><a href="https://doi.org/10.1016/j.cpc.2023.108973">DOI</a></td>
  </tr>
  <tr>
    <td>2024</td>
    <td>High-Frequency Nongyrokinetic Turbulence at Tokamak Edge Parameters</td>
    <td>M. Raeth, <a href="/members/klaus-hallatschek/">K. Hallatschek</a></td>
    <td>Physical Review Letters</td>
    <td><a href="https://doi.org/10.1103/PhysRevLett.133.195101">DOI</a></td>
  </tr>
  <tr>
    <td>2024</td>
    <td>Simulation of ion temperature gradient driven modes with 6D kinetic Vlasov code</td>
    <td>M. Raeth, <a href="/members/klaus-hallatschek/">K. Hallatschek</a>, K. Kormann</td>
    <td>Physics of Plasmas</td>
    <td><a href="https://doi.org/10.1063/5.0197970">DOI</a></td>
  </tr>
  <tr>
    <td>2024</td>
    <td>Surprisingly tight Courant–Friedrichs–Lewy condition in explicit high-order Arakawa schemes</td>
    <td>Mario Raeth, <a href="/members/klaus-hallatschek/">Klaus Hallatschek</a></td>
    <td>Physics of Fluids</td>
    <td><a href="https://doi.org/10.1063/5.0223009">DOI</a></td>
  </tr>
  <tr>
    <td>2012</td>
    <td>Excitation of Geodesic Acoustic Modes by External Fields</td>
    <td><a href="/members/klaus-hallatschek/">K. Hallatschek</a>, G. R. McKee</td>
    <td>Physical Review Letters</td>
    <td><a href="https://doi.org/10.1103/PhysRevLett.109.245001">DOI</a></td>
  </tr>
  <tr>
    <td>2012</td>
    <td>The nonlinear dispersion relation of geodesic acoustic modes</td>
    <td>Robert Hager, <a href="/members/klaus-hallatschek/">Klaus Hallatschek</a></td>
    <td>Physics of Plasmas</td>
    <td><a href="https://doi.org/10.1063/1.4747725">DOI</a></td>
  </tr>
  <tr>
    <td>2007</td>
    <td>Nonlinear three-dimensional flows in magnetized plasmas</td>
    <td><a href="/members/klaus-hallatschek/">K Hallatschek</a></td>
    <td>Plasma Physics and Controlled Fusion</td>
    <td><a href="https://doi.org/10.1088/0741-3335/49/12B/S13">DOI</a></td>
  </tr>
  <tr>
    <td>2004</td>
    <td>Turbulent Saturation of Tokamak-Core Zonal Flows</td>
    <td><a href="/members/klaus-hallatschek/">K. Hallatschek</a></td>
    <td>Physical Review Letters</td>
    <td><a href="https://doi.org/10.1103/PhysRevLett.93.065001">DOI</a></td>
  </tr>
  <tr>
    <td>2001</td>
    <td>Transport Control by Coherent Zonal Flows in the Core/Edge Transitional Regime</td>
    <td><a href="/members/klaus-hallatschek/">K. Hallatschek</a>, D. Biskamp</td>
    <td>Physical Review Letters</td>
    <td><a href="https://doi.org/10.1103/PhysRevLett.86.1223">DOI</a></td>
  </tr>
  </tbody>
</table>
<!-- AUTO:PUBLICATIONS:END -->

## Dissertations

<!-- AUTO:DISSERTATIONS:START -->
<p>No dissertations for this group yet.</p>
<!-- AUTO:DISSERTATIONS:END -->
