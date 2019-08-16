# Terminal colors
export PS1="\[\033[36m\]\u\[\033[m\]@\[\033[32m\]\h:\[\033[33;1m\]\w\[\033[m\]\$ "
export CLICOLOR=1
export LSCOLORS=ExFxBxDxCxegedabagacad

# Bash completion for oc
source <(oc completion bash)

# Custom aliases
alias ls='ls -GFh'
alias ll='ls -la'
alias lt='ls --human-readable --size -1 -S --classify'
alias pg-start="launchctl load ~/Library/LaunchAgents/homebrew.mxcl.postgresql.plist"
alias pg-stop="launchctl unload ~/Library/LaunchAgents/homebrew.mxcl.postgresql.plist"
alias grep="grep --color "

# Vi editing mode for bash
set -o vi