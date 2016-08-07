"""
==============================================================
Denoise images using Adaptive Soft Coefficient Matching (ASCM)
==============================================================

Using the non-local means based adaptive denoising [Coupe11]_ you can denoise
3D or 4D images and boost the SNR of your datasets.

"""

import numpy as np
import matplotlib.pyplot as plt
import nibabel as nib
from dipy.data import fetch_sherbrooke_3shell
from dipy.data import read_sherbrooke_3shell
from dipy.denoise.noise_estimate import estimate_sigma
from time import time
from dipy.denoise.non_local_means import non_local_means
from dipy.denoise.ascm import ascm

"""
Choose one of the data from the datasets in DIPY
"""

fetch_sherbrooke_3shell()
img, gtab = read_sherbrooke_3shell()

data = img.get_data()
affine = img.get_affine()

mask = data[..., 0] > 80
data = data[..., 1]

print("vol size", data.shape)

t = time()

"""
The ``ascm`` function takes two denoised inputs, one more smooth than the other,
for generating these inputs we will use the ``non_local_means`` denoising.
In order to call ``non_local_means`` first you need to estimate the standard
deviation of the noise. We use N=4 since the Sherbrooke dataset was acquired
on a 1.5T Siemens scanner with a 4 array head coil.
"""

sigma = estimate_sigma(data, N=4)

"""
Non-local means with a smaller patch size which implies less smoothing, more
sharpness
"""

den_small = non_local_means(
    data,
    sigma=sigma,
    mask=mask,
    patch_radius=1,
    block_radius=1,
    rician=True)

"""
Non-local means with larger patch size which implies more smoothing, less
sharpness
"""

den_large = non_local_means(
    data,
    sigma=sigma,
    mask=mask,
    patch_radius=2,
    block_radius=1,
    rician=True)

# Now perform the adaptive soft coefficient matching
"""
Now we perform the adaptive soft coefficient matching. Empirically we set the
adaptive parameter h in ascm to be the average of the local noise variance, in
this case the sigma itself.
"""

den_final = np.array(ascm(data, den_small, den_large, sigma[0]))

print("total time", time() - t)

"""
Plot the axial slice of the data, it's denoised output and the residual
"""

axial_middle = data.shape[2] / 2

original = data[:, :, axial_middle].T
final_output = den_final[:, :, axial_middle].T
difference = np.abs(final_output.astype('f8') - original.astype('f8'))
difference[~mask[:, :, axial_middle].T] = 0

fig, ax = plt.subplots(1, 3)
ax[0].imshow(original, cmap='gray', origin='lower')
ax[0].set_title('Original')
ax[1].imshow(final_output, cmap='gray', origin='lower')
ax[1].set_title('ASCM output')
ax[2].imshow(difference, cmap='gray', origin='lower')
ax[2].set_title('Residual')
for i in range(3):
    ax[i].set_axis_off()

plt.savefig('denoised_ascm.png', bbox_inches='tight')

print("The result saved in denoised_ascm.png")

"""
.. figure:: denoised_ascm.png
   :align: center

   **Showing the axial slice without (left) and with (middle) ASCM denoising**.
"""

nib.save(nib.Nifti1Image(den_final, affine), 'denoised_ascm.nii.gz')

print("Saving the entire denoised output in denoised_ascm.nii.gz")
"""
The comparision between the ascm output and the non-local-means.

We see in the figure below that the NLMEANS large (the non-local-means with
larger patch radius) is little oversmoothed, while the NLMEAS small (one
with) leaves some granularity. In comparison the ASCM output is properly
smooth with very little granularity and while preserving the sharpness of
the edges.
"""

fig, ax = plt.subplots(1, 4)
ax[0].imshow(original, cmap='gray', origin='lower')
ax[0].set_title('Original')
ax[1].imshow(den_small[..., axial_middle].T, cmap='gray', origin='lower',
             interpolation='none')
ax[1].set_title('NLMEANS small')
ax[2].imshow(den_large[..., axial_middle].T, cmap='gray', origin='lower',
             interpolation='none')
ax[2].set_title('NLMEANS large')
ax[3].imshow(final_output, cmap='gray', origin='lower', interpolation='none')
ax[3].set_title('ASCM ')
for i in range(4):
    ax[i].set_axis_off()

plt.savefig('ascm_comparison.png', bbox_inches='tight')

print("The result saved in ascm_comparison.png")

"""
.. figure:: ascm_comparision.png
   :align: center

   **Comparing outputs of the NLMEANS and ASCM**.
"""

"""
References
----------

..  [Coupe11] Pierrick Coupe, Jose Manjon, Montserrat Robles, Louis Collins.
    Adaptive Multiresolution Non-Local Means Filter for 3D MR Image Denoising.
    IET Image Processing, Institution of Engineering and Technology,
    2011. <00645538>

"""
