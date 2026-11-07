# Limitaciones conocidas de coldformed

Lo que el paquete no hace o hace de forma simplificada.

- `fsm_assembly.compute_signature_curve_fsm` solo reproduce el modo local: para una C con labios no aparece el mínimo distorsional y a longitudes largas σ_cr crece en vez de aplanarse hacia Euler. Usa el Apéndice 2 para σ_crd y Euler para el global. El bloque de rigidez geométrica de membrana (`include_membrane_kg`, 6e04739) existe en el ensamblado interno, pero `compute_signature_curve_fsm` no lo expone.
- `distortional` cubre C y Z con labio simple a 90°; en flexión se asume ξ_web = 2 (flexión pura). Las dimensiones de línea media se toman como b − t y c − t/2.
- `shear` tiene AISI §G2 (`shear_capacity`) y EN 1993-1-3 §6.1.5 (`shear_capacity_ec3`, alma sin rigidizadores longitudinales, Ec. 6.10a); no hay interacción con el aplastamiento local.
- `Class4Section` idealiza el cajón o la I con espesores de ala y alma (`t_f`, `t_w`, por defecto `t`) y ψ fijos (−1 alma, +1 ala); es una aproximación, no un cálculo de sección eficaz completo.
- `signature_curve` (módulo analítico) es una placa aislada: sus etiquetas «Distortional» y «Global» son regiones de λ, no modos de una sección.
- `web_crippling` incluye cinco conjuntos representativos de coeficientes de la Tabla G5-1, no las cinco tablas completas.
- `perforations`, `galvanizing` y `cost_estimator` son reglas simplificadas y tarifas orientativas.
- El metamodelo `surrogates` tiene errores del orden del 10–20 % por punto; es una herramienta de cribado.
- `fsm_jit` compila con Numba en la primera llamada, que tarda unos segundos.
