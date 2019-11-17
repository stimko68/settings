
# Terminal colors
export PS1="\[\033[36m\]\u\[\033[m\]@\[\033[32m\]\h:\[\033[33;1m\]\w\[\033[m\]\$ "
export CLICOLOR=1
export LSCOLORS=ExFxBxDxCxegedabagacad

# Custom aliases
alias ls='ls -GFh'
alias ll='ls -la'
alias lt='ls --human-readable --size -1 -S --classify'
alias grep="grep --color "

# Vi editing mode for bash
set -o vi

# For Tilix
if [ $TILIX_ID ] || [ $VTE_VERSION ]; then
        source /etc/profile.d/vte.sh
fi
