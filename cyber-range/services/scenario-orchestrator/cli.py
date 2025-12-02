#!/usr/bin/env python3
"""
Simple CLI entry point for scenario orchestrator
Usage:
  python cli.py deploy <scenario>    - Deploy a scenario
  python cli.py destroy              - Destroy infrastructure
  python cli.py status               - Show current outputs
"""

import sys
import argparse
import logging
from orchestrator import Orchestrator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def main():
    parser = argparse.ArgumentParser(
        description='Cyber Range Scenario Orchestrator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py deploy basic_pentest
  python cli.py deploy advanced_multi_team
  python cli.py destroy
  python cli.py status
        """
    )

    parser.add_argument('command', choices=['deploy', 'destroy', 'status'],
                        help='Command to execute')
    parser.add_argument('scenario', nargs='?', default=None,
                        help='Scenario name (required for deploy)')

    args = parser.parse_args()

    try:
        orch = Orchestrator()

        if args.command == 'deploy':
            if not args.scenario:
                print("Error: scenario name required for deploy command")
                sys.exit(1)
            print(f"\n🚀 Deploying scenario: {args.scenario}")
            result = orch.deploy(args.scenario)
            if result['success']:
                print("✅ Deployment successful!")
                if result.get('outputs'):
                    print("\n📋 Outputs:")
                    for key, value in result['outputs'].items():
                        print(f"  {key}: {value}")
            else:
                print(f"❌ Deployment failed: {result.get('error')}")
                sys.exit(1)

        elif args.command == 'destroy':
            print("\n🔥 Destroying infrastructure...")
            result = orch.destroy()
            if result['success']:
                print("✅ Destroy successful!")
            else:
                print(f"❌ Destroy failed: {result.get('error')}")
                sys.exit(1)

        elif args.command == 'status':
            print("\n📊 Current infrastructure status")
            try:
                outputs = orch._get_outputs()
                if outputs:
                    for key, value in outputs.items():
                        print(f"  {key}: {value}")
                else:
                    print("  No active infrastructure found")
            except Exception as e:
                print(f"  Error reading status: {e}")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
