"""Export a person detector (torchvision SSDlite320-MobileNetV3, COCO weights) to ExecuTorch.

    python nightwatch/vision/export_detector.py --backend xnnpack    # CPU: Mac, Linux, Windows
    python nightwatch/vision/export_detector.py --backend qnn        # Hexagon NPU (x86_64 host + QNN SDK)

Only the neural network goes into the .pte (backbone + detection head: the heavy part). The
anchor boxes are fixed for a 320x320 input, so they are computed once here and saved next to
the model; decoding and non-maximum suppression run in plain PyTorch at runtime (detector.py).
Weights: torchvision's pretrained COCO checkpoint (BSD-licensed), downloaded on first run.
Writes models/person_ssdlite_<backend>.pte and models/person_ssdlite_anchors.pt.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import torch
from torch import nn

ROOT = Path(__file__).resolve().parents[2]
SIZE = 320


class DetectorCore(nn.Module):
    """Image (1,3,320,320), already normalized -> (box deltas (1,A,4), class logits (1,A,91))."""

    def __init__(self, model: nn.Module) -> None:
        super().__init__()
        self.backbone = model.backbone
        self.head = model.head

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        features = list(self.backbone(x).values())
        out = self.head(features)
        return out["bbox_regression"], out["cls_logits"]


def load() -> tuple[DetectorCore, torch.Tensor]:
    from torchvision.models.detection import SSDLite320_MobileNet_V3_Large_Weights, ssdlite320_mobilenet_v3_large
    from torchvision.models.detection.image_list import ImageList

    model = ssdlite320_mobilenet_v3_large(weights=SSDLite320_MobileNet_V3_Large_Weights.COCO_V1).eval()
    core = DetectorCore(model).eval()
    with torch.no_grad():
        x = torch.zeros(1, 3, SIZE, SIZE)
        features = list(model.backbone(x).values())
        anchors = model.anchor_generator(ImageList(x, [(SIZE, SIZE)]), features)[0]
    return core, anchors


def export(core: DetectorCore, backend: str) -> Path:
    example = (torch.rand(1, 3, SIZE, SIZE) * 2 - 1,)
    if backend == "xnnpack":
        from executorch.backends.xnnpack.partition.xnnpack_partitioner import XnnpackPartitioner
        from executorch.exir import to_edge_transform_and_lower

        program = torch.export.export(core, example)
        pte = to_edge_transform_and_lower(program, partitioner=[XnnpackPartitioner()]).to_executorch()
    else:
        from executorch.backends.qualcomm.serialization.qc_schema import QcomChipset
        from executorch.backends.qualcomm.utils.utils import (
            generate_htp_compiler_spec,
            generate_qnn_executorch_compiler_spec,
            to_edge_transform_and_lower_to_qnn,
        )

        # fp16 needs no calibration. If the compile rejects it, quantize with QnnQuantizer using
        # a few dozen camera frames (see ExecuTorch Qualcomm docs).
        specs = generate_qnn_executorch_compiler_spec(
            soc_model=QcomChipset.SC8380XP, backend_options=generate_htp_compiler_spec(use_fp16=True))
        pte = to_edge_transform_and_lower_to_qnn(core, example, specs).to_executorch()
    out = ROOT / "models" / f"person_ssdlite_{backend}.pte"
    out.parent.mkdir(exist_ok=True)
    out.write_bytes(pte.buffer)
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB)")
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--backend", choices=["xnnpack", "qnn"], default="xnnpack")
    args = p.parse_args()
    core, anchors = load()
    torch.save(anchors, ROOT / "models" / "person_ssdlite_anchors.pt")
    print(f"anchors: {tuple(anchors.shape)}")
    path = export(core, args.backend)
    if args.backend == "xnnpack":
        from executorch.runtime import Runtime

        x = torch.rand(1, 3, SIZE, SIZE) * 2 - 1
        got = Runtime.get().load_program(str(path)).load_method("forward").execute([x])
        with torch.no_grad():
            want = core(x)
        print("check: max |pte - eager| =", max(float((g - w).abs().max()) for g, w in zip(got, want)))


if __name__ == "__main__":
    main()
