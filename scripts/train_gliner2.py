# scripts/train_gliner2.py
"""
GLiNER2 학습 스크립트 (JSONL 데이터 사용)
"""

from __future__ import annotations

import argparse
from pathlib import Path

from gliner2 import GLiNER2
from gliner2.training.trainer import GLiNER2Trainer, TrainingConfig


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train_data", type=str, required=True, help="Training JSONL file")
    ap.add_argument("--val_data", type=str, default=None, help="Validation JSONL file")
    ap.add_argument(
        "--output_dir", type=str, default="./output", help="Output directory"
    )
    ap.add_argument(
        "--base_model", type=str, default="fastino/gliner2-base-v1", help="Base model"
    )
    ap.add_argument("--num_epochs", type=int, default=20, help="Number of epochs")
    ap.add_argument("--batch_size", type=int, default=16, help="Batch size")
    ap.add_argument(
        "--encoder_lr", type=float, default=1e-5, help="Encoder learning rate"
    )
    ap.add_argument(
        "--task_lr", type=float, default=5e-4, help="Task head learning rate"
    )
    args = ap.parse_args()

    # Load base model
    print(f"Loading base model: {args.base_model}")
    try:
        model = GLiNER2.from_pretrained(args.base_model)
    except Exception as e:
        print(f"Failed to load as GLiNER2 model: {e}")
        print(f"Initializing new GLiNER2 model with encoder: {args.base_model}")
        from gliner2.model import Extractor, ExtractorConfig

        config = ExtractorConfig(model_name=args.base_model)
        model = Extractor(config)

    # Training config
    config = TrainingConfig(
        output_dir=args.output_dir,
        num_epochs=args.num_epochs,
        batch_size=args.batch_size,
        encoder_lr=args.encoder_lr,
        task_lr=args.task_lr,
        save_steps=500,
        eval_steps=500 if args.val_data else None,
        logging_steps=100,
    )

    # Create trainer
    trainer = GLiNER2Trainer(model, config)

    # Train
    print(f"Training on: {args.train_data}")
    if args.val_data:
        print(f"Validation on: {args.val_data}")

    trainer.train(
        train_data=args.train_data,  # JSONL 파일 경로를 직접 전달
        val_data=args.val_data if args.val_data else None,
    )

    # Save final model
    final_path = Path(args.output_dir) / "final_model"
    print(f"Saving final model to: {final_path}")
    model.save_pretrained(str(final_path))
    print("Training complete!")


if __name__ == "__main__":
    main()
