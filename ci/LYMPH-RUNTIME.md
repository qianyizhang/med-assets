# Lymph reconstruction in the software CI probe

This proposed extension reconstructs the compact candidate inside the existing
main-only, manual Actions job from its already pinned published HRA source. It
checks exact byte counts and SHA-256 of the r03 intermediate, source map and
current compact output before serving the candidate only on the ephemeral
loopback server. The intermediate is 14,190,680 bytes; this local output has a
16 MiB verification bound. The network download bound remains 10 MiB per
resource. Temporary recipe receipts are size-bounded and hashed, and no GLB or
receipt is uploaded in the artifact. Captured canvas and full display images,
logs and provenance are uploaded for three days as before; the additional
images depict the unpublished candidate and require independent exposure review
before dispatch. No candidate payload is staged or published by this change.

Identities: published source `7b047002cbb1dc06f37baa441783390d76cdb444b6144d6caa623923707953fd`;
r03 `2f6f65e98ccd280166343fd6a9d1a59f3d5e97830759dd531d80a43f27487194`;
current compact recipe `f89e989450e6f5f64a9d939d135ad0ec17c22e86eee6d9977d46dd68ca542f83`
(7,614,568 bytes). The retained compact comparison is
`882d146ce2b04547e1f45704a414d5d0a059fef7bff980fe7b932148be24314e`
(7,614,472 bytes). Their explanatory metadata differs. Prior Blender
measurements and images remain bound to the retained identity, and are not
asserted for the newly reconstructed bytes.

The front and reverse lit views share camera, projection, lights and background
across source and candidate. Diagnostic normal-material front/back passes use
loaded vertex normals and actual front/back culling, with independent pixel
readback and display matching. These diagnostics intentionally override material
appearance and do not establish the correctness of every normal, culling at
all viewpoints, native UI, production viewer behavior, hardware performance,
or practical memory/load costs. This is headed Firefox/Three with a software
renderer; results must be inspected and are not a GPU or supported-device pass.
Anatomical, clinical and visual acceptance and the unresolved vascular label
remain separate gates. No runtime result exists until the reviewed main-only job
is authorized and run.
