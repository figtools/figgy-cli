Figgy CLI Changelog:

## 1.2.2
- Fixing a bug whereby the latest version of the UI (including OTS work) was not embedded in the released CLI version.

## 1.2.1
- Making `--version` and `--upgrade` commands now consult the current installed figgy-cloud version 
before attempting auto-upgrade.

## 1.2.0
- **Requires Figgy Cloud version 1.1.0**
- Added support for sharing auto-expiring one-read secrets in the figgy ui and cli.
- Stop sharing secrets with your colleagues through email!

## 1.1.3
- Fixing bug with anonymous metric reporting.

## 1.1.2
- Adding Figgy UI tour. 

## 1.1.1
- Reducing log verbosity for the UI when encountering expected errors. 

## 1.1.0
- Adding new `build-cache` command that will force build out figgy's caches ahead of time for a more excellent user
experience (it's also better for demos :smiley:)
- Adding local environment validation. Prevent users with AWS_ prefixed ENV vars from running figgy in certain contexts.

## 1.0.1
- Keyboard interrupts for `figgy ui` commands will now provide a friendly error message. Have a great day!

## 1.0.0
- Figgy 1.0 is out! 
- New `figgy ui` command that will open a local browser window and provide Figgy CLIs functionality in a new beautiful UI!

## 0.1.7
- Updating cryptography package to address another vulnerability

## 0.1.6
- Updating cryptography package to address vulnerability

## 0.1.5
- Testing out pyinstaller 4.0

## 0.1.4
- Fixing a bug with color display on non-truecolor terminals. 

## 0.1.3
- Fixing a display bug with `browse` when users selected delete then select (or the reverse) for a single fig.
- Improving performance of de-selection of nodes in the browse tree.

## 0.1.2
- Clarify some error messaging in the FiggyCLI. Also removing some invalid options from `--configure` command.

## 0.1.1
- Tuning Figgy metric gathering.

## 0.1.0
- Figgy beta release!
- Changes to prevent Linux users from experiencing multiple keychain decrypt prompts during a single command execution.
- Adding support for an ENV variable to prevent constant keyring decrypt prompts. 

## 0.0.66
- Fixing a bug with `list` where the value would always return 'asdf'. This was accidentally left in as an artifact of
troubleshooting.

## 0.0.65
- Fixing issue that could cause a set AWS_PROFILE environment variable to cause errors in figgy.

## 0.0.64
- Adding support to disable version checks.

## 0.0.63
- Fixing bug with --upgrade printing out too much junk.

## 0.0.62 
- Fixing a bug with restore where restored parameters could be missing their KMS Key Id parameter.
- Major refactoring for audit table / restore command / tests

## 0.0.61
- Lots of output & color standardization. Improvements in UX.

## 0.0.60
- Major improvements to Browse command to add dynamic lookups and tracking of marked parameters for deleted or selected parameters

## 0.0.59
- List command has been scrapped and replaced with a much improved user experience allowing dynamic filter, automatic lookups, and sub-search
- `click` library dependency has been removed as a result of abandoning existing List command.

## 0.0.58
- Renaming `cleanup` command as `prune`
- Removing references to `orphaned` parameters and replacing with `stray`.
- E2E Test tweaks.
- Fixing issue with Keyboard Interrupts not properly being caught and gracefully exiting.
- Beginning output standardization across the codebase.

## 0.0.57
- Adding 'version' as a parameter in anonymous error reporting.
- Tweaking figgy color palette
- Fixing bug with `sync` command with `--replication-only` flag when run under the wrong role the user could receive
a stack trace and not a specific error message as intended.

## 0.0.56
- Fixing bug with promote command when using --profile
- Minor tweaks / improvements to the output of some command

## 0.0.55
- Release for testing auto-install script auto-matic upgrades

## 0.0.54
- Working around weird visual artifact issue when selecting colors in 0.0.53

## 0.0.53
- Adding automatic-backup of long-lived ****access keys that could be overwritten by `iam export` command.
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

