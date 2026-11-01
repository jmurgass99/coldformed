// fsmKernel.cpp — C++ WebAssembly kernel for ColdFormed plate elastic buckling
// stress and Winter effective width reduction factor.

extern "C" {

double plateBucklingStress(double E, double t, double b, double k_sigma) {
    const double c_plate = 0.9038136267114746; // pi^2 / (12 * (1 - 0.3^2))
    return c_plate * k_sigma * E * (t * t) / (b * b);
}

double winterRhoUnchecked(double lambda_p) {
    return (lambda_p - 0.22) / (lambda_p * lambda_p);
}

}
