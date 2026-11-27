#!/usr/bin/env python3
"""Inspect, backfill and hydrate med-assets governance records."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"lib"))
from med_assets.governance import GovernanceError,build_catalog,find,show,impact
from med_assets.governance_migration import apply_backfill_plan,hydrate_lfs,write_backfill_plan

def emit(value): print(json.dumps(value,ensure_ascii=False,indent=2))
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--repo",type=Path,default=ROOT)
    commands=parser.add_subparsers(dest="command",required=True)
    commands.add_parser("scan",help="Build a disposable catalog")
    query=commands.add_parser("find");query.add_argument("query");query.add_argument("--domain",choices=("ultrasound-anatomy","body-systems","teaching-assessments"))
    inspect=commands.add_parser("show");inspect.add_argument("identity")
    affected=commands.add_parser("impact");affected.add_argument("identity")
    backfill=commands.add_parser("backfill");backfill.add_argument("action",choices=("plan","apply"))
    backfill.add_argument("--output",type=Path,default=Path(".artifacts/asset-backfill.plan.json"));backfill.add_argument("--plan",type=Path)
    hydrate=commands.add_parser("hydrate");hydrate.add_argument("paths",nargs="+");hydrate.add_argument("--apply",action="store_true")
    args=parser.parse_args();repo=args.repo.resolve()
    try:
        if args.command=="scan": emit(build_catalog(repo).to_dict())
        elif args.command=="find": emit(find(build_catalog(repo),args.query,args.domain))
        elif args.command=="show": emit(show(build_catalog(repo),args.identity))
        elif args.command=="impact": emit(impact(build_catalog(repo),args.identity))
        elif args.command=="backfill" and args.action=="plan":
            output=args.output if args.output.is_absolute() else repo/args.output;plan=write_backfill_plan(repo,output)
            emit({"status":"planned","output":output.relative_to(repo).as_posix(),"proposals":len(plan["proposals"]),
              "consumerCoverage":plan["consumerCoverage"]})
        elif args.command=="backfill" and args.action=="apply":
            if not args.plan: parser.error("backfill apply requires --plan")
            path=args.plan if args.plan.is_absolute() else repo/args.plan
            emit({"status":"applied","records":apply_backfill_plan(repo,path)})
        elif args.command=="hydrate": emit(hydrate_lfs(repo,args.paths,args.apply))
        return 0
    except (GovernanceError,OSError,ValueError,KeyError,TypeError) as exc:
        print(f"asset-governance: {exc}",file=sys.stderr);return 2
if __name__=="__main__": raise SystemExit(main())
