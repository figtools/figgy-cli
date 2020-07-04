Figgy Changelog:

## 0.0.57
- Adding 'version' as a parameter in anonymous error reporting.

## 0.0.56
- Fixing bug with promote command when using --profile
- Minor tweaks / improvements to the output of some command

## 0.0.55
- Release for testing auto-install script auto-matic upgrades

## 0.0.54
- Working around weird visual artifact issue when selecting colors in 0.0.53

## 0.0.53
- Adding automatic-backup of long-lived access keys that could be overwritten by `iam export` command.
- Adding `iam restore` command to restore those access keys to the default profile
- Adding support for ${VARIABLES} in `sync` command with `--replicaion-only` flag. 

## 0.0.52
- Disabling "always upgrade" that was used for testing.

## 0.0.51
- Testing python 3.7.4 instead of 3.8. There may be cython issues with 3.8.

## 0.0.50
- Troubleshooting issues with auto-upgrade when the binary is built via get actions, I have no problem for locally
built binaries.

## 0.0.49
- Forcing mac installs to `/usr/local/bin/figgy`. 

There is no good work-around that I have found that prevents issues with automatic upgrade symlink chaining on MacOs. 
Essentialy `os.path.dirname(sys.executable)` does not return the directory of the symlink on MacOs 
like it does on Windows/Linux. It instead follows the chain of links and returns actual executable's directory. Which 
seems like the right thing to do, except I'd prefer to locate the link instead.

## 0.0.48
- More testing for auto-upgrade. 

## 0.0.47
- More testing for auto-upgrade. 

## 0.0.46
- More testing for auto-upgrade. 

## 0.0.45
- More auto-upgrade testing

## 0.0.44
- More auto-upgrade testing

## 0.0.43
- More auto-upgrade testing / releases

## 0.0.42
- Fixing more install issues.

## 0.0.41
- Addressing issue auto-upgrade on brew-based installations

## 0.0.40
- Releasing to test auto-upgrade and roll-back features

## 0.0.39
- Adding auto-upgrade feature to `figgy`

## 0.0.38
- Forcing a new version to test homebrew versioning support.

## 0.0.37
- Fixing a packaging issue with homebrew installations

## 0.0.36
- Improving ergonoimcs and clarity of the --configure command. 

## 0.0.35
- Fixing a bug with browse where certain figs would get improperly assigned within the browse tree.

## 0.0.34
- Forcing release to address brew issue

## 0.0.33
- Adding a set of default places to search for the figgy.json file to reduce keystrokes.

## 0.0.32
- Testing release pipeline through pypi, brew, etc.

## 0.0.31
- Adding support for `--profile` optional parameter that overrides all authentication schemes and authorizes 
only with the user's locally configured & targeted AWSCLI profile. This will be very useful for CICD builds and for
some teams who only have a single AWS account.

- Renaming `figgy` package to `figcli` to prevent name collission shenanigans with the new `figgy-lib` package.

## 0.0.30a
- Naming figgy.json properties to their new 'figgy'names.

## 0.0.29a
- Fixing a bug with `figgy --configure` when configuring a bastion account for the first time.

## 0.0.28a
- Making `config list` command leverage RBAC limited config view for improved performance.

## 0.0.27a
- Continued Testing of release process
- Plus some other stuff!
- And some other stuff!

## 0.0.1a
- First version!

