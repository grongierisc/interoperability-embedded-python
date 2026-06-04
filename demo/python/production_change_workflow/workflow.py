from __future__ import annotations

import argparse
from pathlib import Path

from settings import prod

from iop import Production, ProductionChangePlan


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plan, apply, verify, or roll back the example production."
    )
    parser.add_argument(
        "action",
        choices=("plan", "review", "apply", "verify", "rollback"),
    )
    parser.add_argument("--plan-file", default="plan.json")
    parser.add_argument("--backup-dir", default=".iop/backups")
    parser.add_argument("--backup", help="Backup directory to restore.")
    parser.add_argument("--allow-destructive", action="store_true")
    args = parser.parse_args()

    plan_file = Path(args.plan_file)

    if args.action == "plan":
        plan = prod.plan()
        print(plan)
        plan.save(plan_file)
        print(f"Wrote {plan_file}")
        return

    if args.action == "review":
        print(ProductionChangePlan.load(plan_file))
        return

    if args.action == "apply":
        plan = ProductionChangePlan.load(plan_file)
        result = prod.apply(
            plan,
            allow_destructive=args.allow_destructive,
            backup_dir=args.backup_dir,
        )
        print(result)
        return

    if args.action == "verify":
        plan = ProductionChangePlan.load(plan_file)
        print(prod.verify(plan))
        return

    if args.action == "rollback":
        if not args.backup:
            parser.error("--backup is required for rollback")
        result = Production.rollback_backup(
            args.backup,
            allow_destructive=args.allow_destructive,
        )
        print(result)


if __name__ == "__main__":
    main()
