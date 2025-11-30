---
title: CDK Steering
inclusion: manual
---
# Technology Stack

## AWS CDK

All examples use the AWS Cloud Development Kit (CDK) to define infrastructure as code. The CDK synthesizes to CloudFormation templates.

## Supported Languages

The repository supports 5 languages with full parity as the goal:

- **TypeScript** - Stable, uses npm/Node.js

## Build Systems & Package Managers

### TypeScript
- Package manager: npm
- Dependencies defined in `package.json`
- Build command: `npm run build`
- Test framework: Jest

## Common CDK Commands

All examples support these standard CDK CLI commands:

```bash
# Install CDK globally
npm install -g aws-cdk

# Synthesize CloudFormation template
cdk synth

# List all stacks
cdk ls

# Deploy stack(s) to AWS
cdk deploy

# Show diff against deployed stack
cdk diff

# Destroy deployed stack(s)
cdk destroy
```

## Configuration Files

- `cdk.json` - CDK toolkit configuration, defines app entry point
- `.gitignore` - Excludes build artifacts, node_modules, cdk.out, etc.
- `.npmignore` (TypeScript) - Excludes source files from npm packages


