# Press Ctrl+G to replace the current zsh buffer with a generated command.
[[ -o interactive ]] || return 0

_ask_widget() {
  [[ -z "$BUFFER" ]] && return
  local cmd
  cmd=$(ask --raw --stream "$BUFFER") || return
  BUFFER="$cmd"
  CURSOR=${#BUFFER}
  zle redisplay
}

zle -N _ask_widget
bindkey '^G' _ask_widget
