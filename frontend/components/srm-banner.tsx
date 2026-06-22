import type { Srm } from "@/lib/types";

/** Loud, unmissable banner when a sample-ratio mismatch is detected. */
export function SrmBanner({ srm }: { srm: Srm | null }) {
  if (!srm || !srm.is_mismatch) {
    return null;
  }
  return (
    <div role="alert" className="rounded-lg border border-red-300 bg-red-50 p-4 text-red-800">
      <p className="font-semibold">⚠ Sample Ratio Mismatch — results are NOT trustworthy</p>
      <p className="mt-1 text-sm">
        The observed split {JSON.stringify(srm.observed)} differs from the intended allocation
        (chi²={srm.chi_square.toFixed(1)}, p={srm.p_value.toExponential(1)}). Fix the assignment
        or logging before trusting any metric below.
      </p>
    </div>
  );
}
