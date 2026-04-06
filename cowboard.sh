#!/usr/bin/env bash
# cowboard — sticky note board in the terminal
# Zero dependencies (no cowsay, no jq, no Python)
# Commands: /<figure>[g|r|b|y] <text>  /rm <id>  /clear  /list  /animals  /colors  /q

set -eo pipefail

PERSIST="$HOME/.cowboard.json"
COLOR_RESET="\033[0m"

# ── colours ───────────────────────────────────────────────────────────────────
color_code() {
  case "$1" in
    green)   printf '\033[32m' ;;
    red)     printf '\033[31m' ;;
    blue)    printf '\033[34m' ;;
    yellow)  printf '\033[33m' ;;
    *)       printf '\033[37m' ;;
  esac
}

# ── built-in cowsay engine ────────────────────────────────────────────────────

# make_bubble <text> <wrap_width>
# Prints the speech bubble lines to stdout
make_bubble() {
  local text="$1"
  local wrap=${2:-40}
  # word-wrap at wrap chars
  local words=($text)
  local lines=()
  local cur=""
  for word in "${words[@]}"; do
    if [[ -z "$cur" ]]; then
      cur="$word"
    elif (( ${#cur} + 1 + ${#word} <= wrap )); then
      cur="$cur $word"
    else
      lines+=("$cur")
      cur="$word"
    fi
  done
  [[ -n "$cur" ]] && lines+=("$cur")

  local n=${#lines[@]}
  local max=0
  for l in "${lines[@]}"; do (( ${#l} > max )) && max=${#l}; done

  # top border
  printf ' '
  printf '%0.s-' $(seq 1 $(( max + 2 )))
  printf '\n'

  if (( n == 1 )); then
    printf '< %-*s >\n' "$max" "${lines[0]}"
  else
    for (( i=0; i<n; i++ )); do
      if (( i == 0 ));       then printf '/ %-*s \\\n' "$max" "${lines[$i]}"
      elif (( i == n-1 ));   then printf '\\ %-*s /\n' "$max" "${lines[$i]}"
      else                        printf '| %-*s |\n' "$max" "${lines[$i]}"
      fi
    done
  fi

  # bottom border
  printf ' '
  printf '%0.s-' $(seq 1 $(( max + 2 )))
  printf '\n'
}

# get_animal <name> <thoughts_char>
# Prints the animal body with $thoughts replaced
get_animal() {
  local name="$1"
  local th="${2:-\\}"
  local eyes="oo"
  local tongue="  "
  case "$name" in
    actually)      cat <<'EOF'
          TH
            TH             .:---------:.
              TH        .:               :.
                    .· __..~~       ~~..__ ·.
               ___________________________________
                |  :   ---     | |     ---   :  |
           __   | :   / @ \    | |    / @ \   : |
          /  \   \:   \___/   /   \   \___/   :/
  _  _  _ |  |    \          /     \          /
 / \/ \/ \|  |    : --------         -------- :
 |  |  | _|_ |    :    o   __________    o    :
 \_/\_/\|    |     :  。 0 |   ||   |  0  。 :
 |       \_  |      :-     \___/\___/      -:
 |   _____   |       .-                   -.
  \     /   /          .-               -.
   \______ /              :-----------:
EOF
      ;;
    alpaca)        cat <<'EOF'
          TH   '^----^'
           TH (◕('人')◕)
              (  8    )        ô
              (    8  )_______(  )
              ( 8      8        )
              (_________________)
                ||          ||
               (||         (||
EOF
      ;;
    beavis.zen)    cat <<'EOF'
   TH         __------~~-,
    TH      ,'            ,
          /               \
         /                :
        |                  '
        |                  |
        |                  |
         |   _--           |
         _| =-.     .-.   ||
         o|/o/       _.   |
         /  ~          \ |
       (____@)  ___~    |
          |_===~~~.`    |
       _______.--~     |
       \________       |
                \      |
              __/-___-- -__
             /            _ \
EOF
      ;;
    blowfish)      cat <<'EOF'
   TH
    TH
               |    .
           .   |L  /|
       _ . |\ _| \--+._/| .
      / ||\| Y J  )   / |/| ./
     J  |)'( |        ` F`.'/
   -<|  F         __     .-<
     | /       .-'. `.  /-. L___
     J \      <    \  | | O\|.-'
   _J \  .-    \/ O | | \  |F
  '-F  -<_.     \   .-'  `-' L__
 __J  _   _.     >-'  )._.   |-'
 `-|.'   /_.           \_|   F
   /.-   .                _.<
  /'    /.'             .'  `\
   /L  /'   |/      _.-'-\
  /'J       ___.---'\|
    |\  .--' V  | `. `
    |/`. `-.     `._)
       / .-.\
       \ (  `\
        `.\
EOF
      ;;
    bong)          cat <<'EOF'
         TH
          TH
            ^__^
    _______/(oo)
/\/(       /(__)
   | W----|| |~|
   ||     || |~|  ~~
             |~|  ~
             |_| o
             |#|/
            _+#+_
EOF
      ;;
    bud-frogs)     cat <<'EOF'
     TH
      TH
          oO)-.                       .-(Oo
         /__  _\                     /_  __\
         \  \(  |     ()~()         |  )/  /
          \__\\ |    (-___-)        | /|__/
          '  '--'    ==`-'==        '--'  '
EOF
      ;;
    bunny)         cat <<'EOF'
  TH
   TH   \
        \ /\
        ( )
      .( o ).
EOF
      ;;
    cheese)        cat <<'EOF'
   TH
    TH
      _____   _________
     /     \_/         |
    |                 ||
    |                 ||
   |    ###\  /###   | |
   |     0  \/  0    | |
  /|                 | |
 / |        <        |\ \
| /|                 | | |
| |     \_______/   |  | |
| |                 | / /
/||                 /|||
   ----------------|
        | |    | |
        ***    ***
       /___\  /___\
EOF
      ;;
    cower)         cat <<'EOF'
     TH
      TH
        ,__, |    |
        (oo)\|    |___
        (__)\|    |   )\_
             |    |_w |  \
             |    |  ||   *

             Cower....
EOF
      ;;
    daemon)        cat <<'EOF'
   TH         ,        ,
    TH       /(        )`
     TH      \ \___   / |
            /- _  `-/  '
           (/\/ \ \   /\
           / /   | `    \
           O O   ) /    |
           `-^--'`<     '
          (_.)  _  )   /
           `.___/`    /
             `-----' /
<----.     __ / __   \
<----|====O)))==) \) /====
<----'    `--' `.__,' \
             |        |
              \       /
        ______( (_  / \______
      ,'  ,-----'   |        \
      `--{__________)        \/
EOF
      ;;
    cow|default)   cat <<'EOF'
        TH   ^__^
         TH  (oo)\_______
            (__)\       )\/\
                ||----w |
                ||     ||
EOF
      ;;
    dragon-and-cow) cat <<'EOF'
                       TH                    ^    /^
                        TH                  / \  // \
                         TH   |\___/|      /   \//  .\
                          TH  /O  O  \__  /    //  | \ \           *----*
                            /     /  \/_/    //   |  \  \          \   |
                            \@___\@`    \/_   //    |   \   \         \/\ \
                           0/0/|       \/_ //     |    \    \         \  \
                       0/0/0/0/|        \///      |     \     \       |  |
                    0/0/0/0/0/_|_ /   (  //       |      \     _\     |  /
                 0/0/0/0/0/0/`/,_ _ _/  ) ; -.    |    _ _\.-~       /   /
                             ,-}        _      *-.|.-~-.           .~    ~
            \     \__/        `/\      /                 ~-. _ .-~      /
             \____(oo)           *.   }            {                   /
             (    (--)          .----~-.\        \-`                 .~
             //__\\  \__ Ack!   ///.----..<        \             _ -~
            //    \\               ///-._ _ _ _ _ _ _{^ - - - - ~
EOF
      ;;
    dragon)        cat <<'EOF'
      TH                    / \  //\
       TH    |\___/|      /   \//  \\
            /0  0  \__  /    //  | \ \
           /     /  \/_/    //   |  \  \
           \@_^_\@'/   \/_   //    |   \   \
           //_^_/     \/_ //     |    \    \
        ( //) |        \///      |     \     \
      ( / /) _|_ /   )  //       |      \     _\
    ( // /) '/,_ _ _/  ( ; -.    |    _ _\.-~        .-~~~^-.
  (( / / )) ,-{        _      `-.|.-~-.           .~         `.
 (( // / ))  '/\      /                 ~-. _ .-~      .-~^-.  \
 (( /// ))      `.   {            }                   /      \  \
  (( / ))     .----~-.\        \-'                 .~         \  `. \^-.
             ///.----..>        \             _ -~             `.  ^-`  ^-_
               ///-._ _ _ _ _ _ _}^ - - - - ~                     ~-- ,.-~
                                                                  /.-~
EOF
      ;;
    elephant-in-snake) cat <<'EOF'
   TH
    TH              ....
           ........    .
          .            .
         .             .
.........              .......
..............................

Elephant inside ASCII snake
EOF
      ;;
    elephant)      cat <<'EOF'
 TH     /\  ___  /\
  TH   // \/   \/ \\
     ((    O O    ))
      \\ /     \ //
       \/  | |  \/
        |  | |  |
        |  | |  |
        |   o   |
        | |   | |
        |m|   |m|
EOF
      ;;
    eyes)          cat <<'EOF'
    TH
     TH
                                   .::!!!!!!!:.
  .!!!!!:.                        .:!!!!!!!!!!!!
  ~~~~!!!!!!.                 .:!!!!!!!!!UWWW$$$
      :$NWX!!:           .:!!!!!!XUWW$$$$$$$$P
      $$$##WX!:      .<!!!!UW$$$$"  $$$$$$$$#
      $$$  $$$UX   :!!UW$$$$$$$$   4$$$$$*
      ^$$B  $$$$\     $$$$$$$$$$$$   d$$R"
        "*bd$$$$      '*$$$$$$$$$$$o+#"
             """"          """""""
EOF
      ;;
    flaming-sheep) cat <<'EOF'
  TH            .    .     .
   TH      .  . .     `  ,
    TH    .; .  : .' :  :  : .
     TH   i..`: i` i.i.,i  i .
      TH   `,--.| i |i|ii|ii|i:
           UooU\.'@@@@@@`.||'
           \__/(@@@@@@@@@@)'
                (@@@@@@@@)
                `YY~~~~YY'
                 ||    ||
EOF
      ;;
    fox)           cat <<'EOF'
         TH     ,-.      .-,
          TH    |-.\\ __ /.-|
           TH   \  `    `  /
                /_     _ \
              <  _`q  p _  >
              <.._=/  \=_. >
                 {`\()/`}`\
                 {      }  \
                 |{    }    \
                 \ '--'   .- \
                 |-      /    \
                 | | | | |     ;
                 | | |.;.,..__ |
               .-"";`         `|
              /    |           /
              `-../____,..---'`
EOF
      ;;
    ghostbusters)  cat <<'EOF'
          TH
           TH
            TH          __---__
                    _-       /--______
               __--( /     \ )XXXXXXXXXXX\v.
             .-XXX(   O   O  )XXXXXXXXXXXXXXX-
            /XXX(       U     )        XXXXXXX\
          /XXXXX(              )--_  XXXXXXXXXXX\
         /XXXXX/ (      O     )   XXXXXX   \XXXXX\
         XXXXX/   /            XXXXXX   \__ \XXXXX
         XXXXXX__/          XXXXXX         \__---->
 ---___  XXX__/          XXXXXX      \__         /
   \-  --__/   ___/\  XXXXXX            /  ___--/=
    \-\    ___/    XXXXXX              '--- XXXXXX
       \-\/XXX\ XXXXXX                      /XXXXX
         \XXXXXXXXX   \                    /XXXXX/
          \XXXXXX      >                 _/XXXXX/
            \XXXXX--__/              __-- XXXX/
             -XXXXXXXX---------------  XXXXXX-
                \XXXXXXXXXXXXXXXXXXXXXXXXXX/
                  ""VXXXXXXXXXXXXXXXXXXV""
EOF
      ;;
    head-in)       cat <<'EOF'
    TH
     TH
    ^__^         /
    (oo)\_______/  _________
    (__)\       )=(  ____|_ \_____
        ||----w |  \ \     \_____ |
        ||     ||   ||           ||
EOF
      ;;
    hellokitty)    cat <<'EOF'
  TH
   TH
      /\_)o<
     |      \
     | O . O|
      \_____/
EOF
      ;;
    kiss)          cat <<'EOF'
     TH
      TH
             ,;;;;;;;,
            ;;;;;;;;;;;,
           ;;;;;'_____;'
           ;;;(/))))|((\\
           _;;((((((|))))
          / |_\\\\\\\\\\\\\\\\
     .--~(  \ ~))))))))))))
    /     \  `\-(((((((((((\\
    |    | `\   ) |\       /|)
     |    |  `. _/  \_____/ |
      |    , `\~            /
       |    \  \           /
      | `.   `\|          /
      |   ~-   `\        /
       \____~._/~ -_,   (\
        |-----|\   \    ';;
       |      | :;;;'     \
      |  /    |            |
      |       |            |
EOF
      ;;
    kitty)         cat <<'EOF'
     TH
      TH
       ("`-'  '-/") .___..--' ' "`-._
         ` *_ *  )    `-.   (      ) .`-.__. `)
         (_Y_.) ' ._   )   `._` ;  `` -. .-'
      _.. `--'_..-_/   /--' _ .' ,4
   ( i l ),-''  ( l i),'  ( ( ! .-'
EOF
      ;;
    koala)         cat <<'EOF'
  TH
   TH
       ___
     {~._.~}
      ( Y )
     ()~*~()
     (_)-(_)
EOF
      ;;
    kosh)          cat <<'EOF'
    TH
     TH
      TH
  ___       _____     ___
 /   \     /    /|   /   \
|     |   /    / |  |     |
|     |  /____/  |  |     |
|     |  |    |  |  |     |
|     |  | {} | /   |     |
|     |  |____|/    |     |
|     |    |==|     |     |
|      \___________/      |
|                         |
|                         |
EOF
      ;;
    llama)         cat <<'EOF'
  TH
   TH
       (\/)
      (_o |
       /  |
       \  \______
        \        )o
         /|----- |
         \|     /|
EOF
      ;;
    luke-koala)    cat <<'EOF'
  TH
   TH          .
       ___   //
     {~._.~}//
      ( Y )K/
     ()~*~()
     (_)-(_)
     Luke
     Skywalker
     koala
EOF
      ;;
    mech-and-cow)  cat <<'EOF'
                  TH                ,-----.
                   TH               |     |
                    TH           ,--|     |-.
                         __,----|  |     | |
                       ,;::     |  `_____' |
                       `._______|    i^i   |
                                `----| |---'| .
                           ,-------._| |== ||//
                           |       |_|P`.  /'/
                           `-------' 'Y Y/'/'
                                     .==\ /_\
   ^__^                             /   /'|  `i
   (oo)\_______                   /'   /  |   |
   (__)\       )\/\             /'    /   |   `i
       ||----w |           ___,;`----'.___L_,-'`\__
       ||     ||          i_____;----.____i""\____\
EOF
      ;;
    meow)          cat <<'EOF'
  TH
   TH ,   _ ___.--'''`--''//-,-_--_.
      \`"' ` || \\ \ \\/ / // / ,-\\`,_
     /'`  \ \ || Y  | \|/ / // / - |__ `-,
    /@"\  ` \ `\ |  | ||/ // | \/  \  `-._`-,_.,
   /  _.-. `.-\,___/\ _/|_/_\_\/|_/ |     `-._._)
   `-'``/  /  |  // \__/\__  /  \__/ \
        `-'  /-\/  | -|   \__ \   |-' |
          __/\ / _/ \/ __,-'   ) ,' _|'
         (((__/(((_.' ((___..-'((__,'
EOF
      ;;
    milk)          cat <<'EOF'
 TH     ____________
  TH    |__________|
      /           /\
     /           /  \
    /___________/___/|
    |          |     |
    |  ==\ /== |     |
    |   O   O  | \ \ |
    |     <    |  \ \|
   /|          |   \ \
  / |  \_____/ |   / /
 / /|          |  / /|
/||\|          | /||\\/
    -------------|
        | |    | |
       <__/    \__>
EOF
      ;;
    moofasa)       cat <<'EOF'
       TH    ____
        TH  /    \
          | ^__^ |
          | (oo) |______
          | (__) |      )\/\
           \____/|----w |
                ||     ||

                Moofasa
EOF
      ;;
    moose)         cat <<'EOF'
  TH
   TH   \_\_    _/_/
    TH      \__/
           (oo)\_______
           (__)\       )\/\
               ||----w |
               ||     ||
EOF
      ;;
    mutilated)     cat <<'EOF'
       TH   \_______
 v__v   TH  \   O   )
 (oo)      ||----w |
 (__)      ||     ||  \/\
EOF
      ;;
    ren)           cat <<'EOF'
   TH
    TH
    ____
   /# /_\_
  |  |/o\o\
  |  \\\_/_/
 / |_   |
|  ||\_ ~|
|  ||| \/
|  |||_
 \//  |
  ||  |
  ||_  \
  \_|  o|
  /\___/
 /  ||||__
    (___)_)
EOF
      ;;
    sheep)         cat <<'EOF'
  TH
   TH
       __
      UooU\.'@@@@@@`.
      \__/(@@@@@@@@@@)
           (@@@@@@@@)
           `YY~~~~YY'
            ||    ||
EOF
      ;;
    skeleton)      cat <<'EOF'
          TH      (__)
           TH     /oo|
            TH   (_"_)*+++++++++*
                   //I#\\\\\\\\I\
                   I[I|I|||||I I `
                   I`I'///'' I I
                   I I       I I
                   ~ ~       ~ ~
                     Scowleton
EOF
      ;;
    small)         cat <<'EOF'
       TH   ,__,
        TH  (oo)____
           (__)    )\
               ||--|| *
EOF
      ;;
    stegosaurus)   cat <<'EOF'
TH                             .       .
 TH                           / `.   .' "
  TH                  .---.  <    > <    >  .---.
   TH                 |    \  \ - ~ ~ - /  /    |
         _____          ..-~             ~-..-~
        |     |   \~~~\.'                    `./~~~/
       ---------   \__/                        \__/
      .'  O    \     /               /       \  "
     (_____,    `._.'               |         }  \/~~~/
      `----.          /       }     |        /    \__/
            `-.      |       /      |       /      `. ,~~|
                ~-.__|      /_ - ~ ^|      /- _      `..-'
                     |     /        |     /     ~-.     `-. _  _  _
                     |_____|        |_____|         ~ - . _ _ _ _ _>
EOF
      ;;
    stimpy)        cat <<'EOF'
  TH     .    _  .
   TH    |\_|/__/|
       / / \/ \  \
      /__|O||O|__ \
     |/_ \_/\_/ _\ |
     | | (____) | ||
     \/\___/\__/  //
     (_/         ||
      |          ||
      |          ||\
       \        //_/
        \______//
       __ || __||
      (____(____)
EOF
      ;;
    supermilker)   cat <<'EOF'
  TH   ^__^
   TH  (oo)\_______        ________
      (__)\       )\/\    |Super |
          ||----W |       |Milker|
          ||    UDDDDDDDDD|______|
EOF
      ;;
    surgery)       cat <<'EOF'
          TH           \  /
           TH           \/
               (__)    /\
               (oo)   O  O
               _\/_   //
         *    (    ) //
          \  (\\\    //
           \(  \\    )
            (   \\   )   /\
  ___[\______/^^^^^^^\__/) o-)__
 |\__[=======______//________)__\
 \|_______________//____________|
     |||      || //||     |||
     |||      || @.||     |||
      ||      \/  .\/      ||
                 . .
                '.'.`

            COW-OPERATION
EOF
      ;;
    sus)           cat <<'EOF'
   TH
    TH  .------.
      .---.    \
     ( oo  )   +---\
      `---'    |  |
               |  |
               +---/
      \__/  \__/
EOF
      ;;
    three-eyes)    cat <<'EOF'
        TH  ^___^
         TH (ooo)\_______
           (___)\       )\/\
                 ||----w |
                ||     ||
EOF
      ;;
    turkey)        cat <<'EOF'
  TH                                  ,+*^^*+___+++_
   TH                           ,*^^^^              )
    TH                       _+*                     ^**+_
     TH                    +^       _ _++*+_+++_,         )
              _+^^*+_    (     ,+*^ ^          \+_        )
             {       )  (    ,(    ,_+--+--,      ^)      ^\
            { (@)    } f   ,(  ,+-^ __*_*_  ^^\\_   ^\       )
           {:;-/    (_+*-+^^^^^+*+*<_ _++_)_    )    )      /
          ( /  (    (        ,___    ^*+_+* )   <    <      \
           U _/     )    *--<  ) ^\-----++__)   )    )       )
            (      )  _(^)^^))  )  )\^^^^^))^*+/    /       /
          (      /  (_))_^)) )  )  ))^^^^^))^^^)__/     +^^
         (     ,/    (^))^))  )  ) ))^^^^^^^))^^)       _)
          *+__+*       (_))^)  ) ) ))^^^^^^))^^^^^)____*^
          \             \_)^)_)) ))^^^^^^^^^^))^^^^)
           (_             ^\__^^^^^^^^^^^^))^^^^^^^)
             ^\___            ^\__^^^^^^))^^^^^^^^)\
                  ^^^^^\\uuu/^^\uuu/^^^^^\^\^\^\^\^\^\
                     ___) >____) >___   ^\_\_\_\_\_\_\)
                    ^^^//\\_^^//\\_^       ^(\\_\_\_\)
                      ^^^ ^^ ^^^ ^
EOF
      ;;
    turtle)        cat <<'EOF'
    TH                                  ___-------___
     TH                             _-~~             ~~-_
      TH                         _-~                    /~-_
             /^\__/^\         /~  \                   /    \
           /|  O|| O|        /      \_______________/        \
          | |___||__|      /       /                \          \
          |          \    /      /                    \          \
          |   (_______) /______/                        \_________ \
          |         / /         \                      /            \
           \         \^\         \                  /               \     /
             \         ||           \______________/      _-_       //\__//
               \       ||------_-~~-_ ------------- \ --/~   ~\    || __/
                 ~-----||====/~     |==================|       |/~~~~~
                  (_(__/  ./     /                    \_\      \.
                         (_(___/                         \_____)_)
EOF
      ;;
    tux)           cat <<'EOF'
   TH
    TH
        .--.
       |o_o |
       |:_/ |
      //   \ \
     (|     | )
    /'\_   _/`\
    \___)=(___/

EOF
      ;;
    udder)         cat <<'EOF'
  TH
   TH    (__)
        (oo)\
       ('') \---------
            \           \
           |          |\
           ||---(  )_|| *
           ||    UU  ||
           ==        ==
EOF
      ;;
    vader-koala)   cat <<'EOF'
   TH
    TH        .
     .---.  //
    Y|o o|Y//
   /_(i=i)K/
   ~()~*~()~
    (_)-(_)

     Darth
     Vader
     koala
EOF
      ;;
    vader)         cat <<'EOF'
        TH    ,-^-.
         TH   !oYo!
          TH /./=\.\\______
               ##        )\/\
                ||-----w||
                ||      ||

               Cowth Vader
EOF
      ;;
    www)           cat <<'EOF'
        TH   ^__^
         TH  (oo)\_______
            (__)\       )\/\
                ||--WWW |
                ||     ||
EOF
      ;;
    cupcake)       cat <<'EOF'
         TH
           TH
             TH
                                        &&,     ..&&*
                               @&&&&#       &%      ..&&
                           &&&      &&/ &&&&   %/.   .@&
                         &&    (((&             */   ..&
                        &.                 &&&       .#&&.,&&&&,
                  .&&&&&&               .&&.       .* ,%    ....&&
              .&&(             %&(            .&.   *(((       ..&&
            &&.   &,%    @(**.          &                   @&, ..&&
           &&   &,#                  &((         /#      &%&,    .....%&&&
           &                         #           &/#            .. .......&&&
         &&&%                     .@&&                       &.        **#..(
     (&&                   &///&                                        &*,...
   &&              &(&.                    &,@                            ....
  &&   ///.        (&           &(((.    *,.                  /.           ...
 &#   @/@                     .                     &(&       .#.&         ...
/&          .,           /(                &///&     #(                   ....
 &           .,          &*@          ,                                  .....
 &&                        &  .....  ..... ..,.. ....                   .....
  &@                                                                  ......
   &&           &&(.,.,./**********************/****/*//*(&&*        .....
     .&&&@/,..,,,*******/*****/*****************************////////////&%
         #&,.,/****/**********/*************************/*****/////////&&
          &&.,****************/********************************///////&&
           &&.*/*********/***************/****/****/**********///////%&
            &&,******,&&&&&&&*******/****/****/******&&&&&&&**//////*&(
            *&.*****&&   @&&&&&*****/****/*********&&   &&&&&&//////&&
             &&,***(&&&&&&&&&&&&****/****/********#&&&&&&&&&&&&////&&
              &&****&&&&&&&&&&&*****/*************/&&&&&&&&&&&////&&
               &&*(((((&&&&&*********((((((((%*******,&&&&&(((((//&
                &(*************/****/&((((((#/**************/////&&
                (&*/***/*******/****/**,%&,****************/////&&
                 &&********/********/************/***/*****////&&
                   &&&&,************/*****************/////%&&&%
                          &&&&&&&&&&&&&&&&&&&&&&&&&&&&&@
EOF
      ;;
    *)
      # fallback to default cow
      cat <<'EOF'
        TH   ^__^
         TH  (oo)\_______
            (__)\       )\/\
                ||----w |
                ||     ||
EOF
      ;;
  esac
}

# moo <figure> <text>
# Full cowsay equivalent: bubble + animal
moo() {
  local figure="$1"
  local text="$2"
  local wrap="${3:-40}"
  local bubble
  bubble=$(make_bubble "$text" "$wrap")
  local animal
  animal=$(get_animal "$figure")
  # Replace TH placeholder: first occurrence → \, subsequent → space
  local out=""
  while IFS= read -r line; do
    out+="${line//TH/\\}"$'\n'
  done <<< "$animal"
  printf '%s\n%s' "$bubble" "$out"
}

# list all figure names
list_figures() {
  echo "actually alpaca beavis.zen blowfish bong bud-frogs bunny cheese
cower cow cupcake daemon default dragon-and-cow dragon elephant-in-snake
elephant eyes flaming-sheep fox ghostbusters head-in hellokitty kiss kitty
koala kosh llama luke-koala mech-and-cow meow milk moofasa moose mutilated
ren sheep skeleton small stegosaurus stimpy supermilker surgery sus
three-eyes turkey turtle tux udder vader-koala vader www" | tr ' ' '\n' | sort
}

figure_valid() {
  list_figures | grep -qx "$1"
}

run_cowsay() {
  local figure="$1" text="$2" wrap="${3:-40}"
  moo "$figure" "$text" "$wrap"
}

# ── persistence (pure bash, no jq) ───────────────────────────────────────────
# Format: one note per line, tab-separated: id<TAB>figure<TAB>color<TAB>text<TAB>rendered
# rendered has newlines encoded as \n

encode() { printf '%s' "$1" | tr '\n' $'\x01'; }
decode() { printf '%s' "$1" | tr $'\x01' '\n'; }

init_store() {
  [[ -f "$PERSIST" ]] || printf '' > "$PERSIST"
}

next_id() {
  local max=0 id
  while IFS=$'\t' read -r id _rest; do
    (( id > max )) && max=$id
  done < "$PERSIST"
  echo $(( max + 1 ))
}

save_note() {
  local id="$1" figure="$2" color="$3" text="$4" rendered="$5"
  local enc_rendered enc_text
  enc_rendered=$(encode "$rendered")
  enc_text=$(encode "$text")
  printf '%s\t%s\t%s\t%s\t%s\n' "$id" "$figure" "$color" "$enc_text" "$enc_rendered" >> "$PERSIST"
}

remove_note() {
  local id="$1"
  local tmp
  tmp=$(mktemp)
  while IFS=$'\t' read -r nid rest; do
    [[ "$nid" != "$id" ]] && printf '%s\t%s\n' "$nid" "$rest"
  done < "$PERSIST" > "$tmp"
  mv "$tmp" "$PERSIST"
}

note_exists() {
  local id="$1"
  while IFS=$'\t' read -r nid _rest; do
    [[ "$nid" == "$id" ]] && return 0
  done < "$PERSIST"
  return 1
}

clear_all_notes() {
  printf '' > "$PERSIST"
}

# ── command parser ────────────────────────────────────────────────────────────
parse_cmd() {
  local raw="$1"
  PARSE_FIGURE="" PARSE_COLOR="default" PARSE_TEXT=""
  raw="${raw#/}"
  local figure_part="${raw%% *}"
  local rest="${raw#* }"
  [[ "$figure_part" == "$raw" ]] && return 1
  [[ -z "$rest" ]] && return 1
  PARSE_TEXT="$rest"
  local last="${figure_part: -1}"
  case "$last" in
    g) PARSE_COLOR="green";  PARSE_FIGURE="${figure_part%?}" ;;
    r) PARSE_COLOR="red";    PARSE_FIGURE="${figure_part%?}" ;;
    b) PARSE_COLOR="blue";   PARSE_FIGURE="${figure_part%?}" ;;
    y) PARSE_COLOR="yellow"; PARSE_FIGURE="${figure_part%?}" ;;
    *)  PARSE_COLOR="default"; PARSE_FIGURE="$figure_part" ;;
  esac
  [[ -z "$PARSE_FIGURE" ]] && return 1
  return 0
}

# ── display ───────────────────────────────────────────────────────────────────

_last_cols=0
_last_rows=0
_last_note_sig=""

draw_divider() {
  local cols; cols=$(tput cols)
  printf '%*s\n' "$cols" '' | tr ' ' '─'
}

note_width() {
  local max=0 len
  while IFS= read -r line; do
    len=${#line}; (( len > max )) && max=$len
  done <<< "$1"
  echo $max
}

note_height() {
  local lines; lines=$(printf '%s' "$1" | wc -l)
  echo $(( lines + 1 ))
}

render_note_at() {
  local row="$1" col="$2" color="$3" id="$4" rendered="$5"
  local cc; cc=$(color_code "$color")
  local r=$row
  printf "${cc}"
  while IFS= read -r line; do
    tput cup "$r" "$col"
    printf '%s' "$line"
    (( r++ ))
  done <<< "$rendered"
  tput cup "$r" "$col"
  printf '[%s]' "$id"
  printf "${COLOR_RESET}"
}

compute_layout() {
  local cols="$1" canvas_rows="$2"
  L_ids=(); L_colors=(); L_rendereds=(); L_rows=(); L_cols=(); L_widths=(); L_heights=()

  [[ ! -s "$PERSIST" ]] && return

  local raw_ids=() raw_colors=() raw_rendereds=() raw_widths=() raw_heights=()
  while IFS=$'\t' read -r nid nfigure ncolor ntext nrendered; do
    local rendered; rendered=$(decode "$nrendered")
    local nw nh
    nw=$(note_width "$rendered")
    nh=$(note_height "$rendered")
    raw_ids+=("$nid"); raw_colors+=("$ncolor"); raw_rendereds+=("$rendered")
    raw_widths+=("$nw"); raw_heights+=("$nh")
  done < "$PERSIST"

  local n=${#raw_ids[@]}
  (( n == 0 )) && return

  local GAP=2
  # Estimate number of columns using median width
  local sorted_w=("${raw_widths[@]}")
  IFS=$'\n' sorted_w=($(printf '%s\n' "${sorted_w[@]}" | sort -n)); unset IFS
  local median_w=${sorted_w[$(( n / 2 ))]}
  local num_cols=$(( cols / (median_w + GAP + 4) ))
  (( num_cols < 1 )) && num_cols=1
  (( num_cols > n )) && num_cols=$n

  # col_x is dynamic: starts at 0 and advances by actual max note width in that column + GAP
  local col_y=() col_x=() col_max_w=()
  for (( c=0; c<num_cols; c++ )); do
    col_y[$c]=0; col_max_w[$c]=0
  done
  # First pass: assign notes to columns, compute col_x from actual widths
  local assign=()
  for (( i=0; i<n; i++ )); do
    local best_col=0
    for (( c=1; c<num_cols; c++ )); do
      (( col_y[c] < col_y[best_col] )) && best_col=$c
    done
    assign+=("$best_col")
    (( raw_widths[i] > col_max_w[best_col] )) && col_max_w[$best_col]=${raw_widths[i]}
    col_y[$best_col]=$(( col_y[$best_col] + raw_heights[i] + 1 ))
  done
  # Compute col_x from actual max widths
  col_x[0]=0
  for (( c=1; c<num_cols; c++ )); do
    col_x[$c]=$(( col_x[c-1] + col_max_w[c-1] + GAP ))
  done
  # Check last column fits on screen; if not reduce num_cols and redo
  while (( num_cols > 1 && col_x[num_cols-1] + col_max_w[num_cols-1] > cols )); do
    (( num_cols-- ))
    col_x[0]=0
    for (( c=1; c<num_cols; c++ )); do
      col_x[$c]=$(( col_x[c-1] + col_max_w[c-1] + GAP ))
    done
  done

  # Second pass: actually record layout with correct positions
  for (( c=0; c<num_cols; c++ )); do col_y[$c]=0; done
  for (( i=0; i<n; i++ )); do
    local best_col=0
    for (( c=1; c<num_cols; c++ )); do
      (( col_y[c] < col_y[best_col] )) && best_col=$c
    done
    local pr=${col_y[$best_col]} pc=${col_x[$best_col]}
    if (( pr + raw_heights[i] <= canvas_rows )); then
      L_ids+=("${raw_ids[$i]}"); L_colors+=("${raw_colors[$i]}")
      L_rendereds+=("${raw_rendereds[$i]}")
      L_rows+=("$pr"); L_cols+=("$pc")
      L_widths+=("${raw_widths[$i]}"); L_heights+=("${raw_heights[$i]}")
    fi
    col_y[$best_col]=$(( col_y[$best_col] + raw_heights[i] + 1 ))
  done
}

note_sig() {
  local sig="" i
  for (( i=0; i<${#L_ids[@]}; i++ )); do
    sig+="${L_ids[$i]}:${L_rows[$i]}:${L_cols[$i]} "
  done
  echo "$sig"
}

draw_bar() {
  local rows="$1"
  tput cup $(( rows - 6 )) 0; draw_divider
  tput cup $(( rows - 5 )) 0; printf '  /tux Hello  /dragonr URGENT  /tuxg Note  /rm <id>  /clear  /list  /animals  /colors  /q'
  tput cup $(( rows - 4 )) 0; draw_divider
  tput cup $(( rows - 3 )) 0; tput el
  tput cup $(( rows - 2 )) 0; tput el
}

redraw() {
  local cols rows
  cols=$(tput cols); rows=$(tput lines)
  local canvas_rows=$(( rows - 6 ))
  local size_changed=0
  (( cols != _last_cols || rows != _last_rows )) && size_changed=1
  _last_cols=$cols; _last_rows=$rows

  local L_ids=() L_colors=() L_rendereds=() L_rows=() L_cols=() L_widths=() L_heights=()
  compute_layout "$cols" "$canvas_rows"
  local new_sig; new_sig=$(note_sig)

  if (( size_changed )) || [[ "$new_sig" != "$_last_note_sig" ]]; then
    clear
    local count=${#L_ids[@]}
    if (( count == 0 )); then
      tput cup 1 2; printf 'No notes. Type a message or /tux Hello'
    else
      for (( i=0; i<count; i++ )); do
        render_note_at "${L_rows[$i]}" "${L_cols[$i]}" "${L_colors[$i]}" "${L_ids[$i]}" "${L_rendereds[$i]}"
      done
    fi
    draw_bar "$rows"
    _last_note_sig="$new_sig"
  fi
}

# ── list / info commands ──────────────────────────────────────────────────────
cmd_list() {
  echo ""
  if [[ ! -s "$PERSIST" ]]; then
    echo "  No notes."
  else
    while IFS=$'\t' read -r nid nfigure ncolor ntext _rest; do
      local text; text=$(decode "$ntext")
      printf '  [%s] %s (%s): %s\n' "$nid" "$nfigure" "$ncolor" "$text"
    done < "$PERSIST"
  fi
  echo ""
}

# ── animal picker ────────────────────────────────────────────────────────────
pick_animal() {
  # Returns the chosen figure name on stdout, or empty string if cancelled.
  local -a animals=()
  while IFS= read -r f; do animals+=("$f"); done < <(list_figures)
  local n=${#animals[@]}
  local sel=0
  local cols rows
  cols=$(tput cols); rows=$(tput lines)

  # Layout: figure out how many columns fit
  local max_w=0
  for f in "${animals[@]}"; do (( ${#f} > max_w )) && max_w=${#f}; done
  local cell_w=$(( max_w + 4 ))  # padding + index highlight space
  local ncols=$(( cols / cell_w ))
  (( ncols < 1 )) && ncols=1
  local nrows=$(( (n + ncols - 1) / ncols ))

  # Draw picker over canvas area
  _draw_picker() {
    local start_row=1
    clear
    tput cup 0 2; printf "\033[1mPick an animal\033[0m  (arrows=move  Enter=select  Esc=cancel)"
    local i
    for (( i=0; i<n; i++ )); do
      local r=$(( start_row + i / ncols ))
      local c=$(( (i % ncols) * cell_w ))
      tput cup "$r" "$c"
      if (( i == sel )); then
        printf "\033[7m %-*s \033[0m" $(( cell_w - 2 )) "${animals[$i]}"
      else
        printf " %-*s " $(( cell_w - 2 )) "${animals[$i]}"
      fi
    done
    # restore bottom bar
    draw_bar "$rows"
  }

  _draw_picker
  tput civis  # hide cursor during navigation

  local result=""
  while true; do
    local key seq
    IFS= read -r -s -n1 key
    if [[ "$key" == $'\x1b' ]]; then
      IFS= read -r -s -n1 -t 0.1 seq
      if [[ "$seq" == "[" ]]; then
        IFS= read -r -s -n1 -t 0.1 seq
        case "$seq" in
          A) (( sel > 0 )) && (( sel -= ncols )); (( sel < 0 )) && sel=0 ;;          # Up
          B) (( sel + ncols < n )) && (( sel += ncols )) ;;                            # Down
          C) (( sel + 1 < n )) && (( sel++ )) ;;                                       # Right
          D) (( sel > 0 )) && (( sel-- )) ;;                                           # Left
        esac
        _draw_picker
      else
        # plain Escape — cancel
        result=""; break
      fi
    elif [[ "$key" == "" || "$key" == $'\n' ]]; then
      result="${animals[$sel]}"; break
    elif [[ "$key" == "q" || "$key" == $'\x03' ]]; then
      result=""; break
    fi
  done

  tput cnorm  # restore cursor
  printf '%s' "$result"
}

# ── main loop ─────────────────────────────────────────────────────────────────
show_error() {
  local rows; rows=$(tput lines)
  tput cup $(( rows - 2 )) 0; tput el; printf "\033[31m  %s\033[0m" "$1"
  tput cup $(( rows - 3 )) 2
}

clear_error() {
  local rows; rows=$(tput lines)
  tput cup $(( rows - 2 )) 0; tput el
  tput cup $(( rows - 1 )) 0; tput el
  tput cup $(( rows - 3 )) 2
}

main() {
  init_store
  local _dirty=1

  # Persist command history across sessions
  HISTFILE="$HOME/.cowboard_history"
  HISTSIZE=500
  history -r "$HISTFILE" 2>/dev/null || true

  trap '_dirty=1; redraw; local rows; rows=$(tput lines); tput cup $(( rows - 3 )) 2; printf "❯ "' SIGWINCH
  trap 'history -w "$HISTFILE"' EXIT

  while true; do
    if (( _dirty )); then redraw; _dirty=0; fi

    local rows; rows=$(tput lines)
    tput cup $(( rows - 3 )) 0; tput el
    IFS= read -e -r -p "❯ " input || { echo ""; break; }
    [[ -n "$input" ]] && history -s "$input"

    input="${input#"${input%%[![:space:]]*}"}"
    input="${input%"${input##*[![:space:]]}"}"
    [[ -z "$input" ]] && continue

    # clear any previous error on new command
    clear_error

    if [[ "$input" == "/q" || "$input" == "/quit" || "$input" == "/exit" ]]; then clear; break; fi

    if [[ "$input" == "/list" ]]; then
      cmd_list; read -r -p "  Press enter to continue..." _; _dirty=1; continue
    fi

    if [[ "$input" == "/colors" ]]; then
      echo ""
      printf "  $(color_code green)g  green${COLOR_RESET}\n"
      printf "  $(color_code red)r  red${COLOR_RESET}\n"
      printf "  $(color_code blue)b  blue${COLOR_RESET}\n"
      printf "  $(color_code yellow)y  yellow${COLOR_RESET}\n"
      printf "  $(color_code default)(none)  default${COLOR_RESET}\n"
      echo ""
      read -r -p "  Press enter to continue..." _; _dirty=1; continue
    fi

    if [[ "$input" == "/animals" ]]; then
      local picked; picked=$(pick_animal)
      _dirty=1
      if [[ -n "$picked" ]]; then
        # Redraw board, then prompt with /<animal> pre-typed; user adds text + Enter
        redraw; _dirty=0
        local rows; rows=$(tput lines)
        tput cup $(( rows - 3 )) 0; tput el
        printf "❯ /$picked "
        local rest=""
        IFS= read -e -r rest
        input="/$picked $rest"
        [[ -n "$input" ]] && history -s "$input"
        input="${input#"${input%%[![:space:]]*}"}"
        input="${input%"${input##*[![:space:]]}"}"
        [[ -z "$input" ]] && continue
        clear_error
        # fall through to command handling below
      else
        continue
      fi
    fi

    if [[ "$input" =~ ^/rm[[:space:]]+([0-9]+)$ ]]; then
      local rm_id="${BASH_REMATCH[1]}"
      if note_exists "$rm_id"; then
        remove_note "$rm_id"; _last_note_sig=""; _dirty=1
      else
        show_error "No note with id $rm_id"
      fi
      continue
    fi

    if [[ "$input" == "/clear" ]]; then
      tput cup $(( rows - 3 )) 0
      tput el
      printf "  Remove ALL notes? [y/N] "
      local confirm=""; IFS= read -r confirm
      if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
        clear_all_notes; _last_note_sig=""; _dirty=1
      fi
      continue
    fi

    # plain text → default cow
    [[ "$input" != /* ]] && input="/cow $input"

    if [[ "$input" == /* ]]; then
      if ! parse_cmd "$input"; then
        show_error "Usage: /<figure>[g|r|b|y] <text>"; continue
      fi

      local figure="$PARSE_FIGURE" color="$PARSE_COLOR" text="$PARSE_TEXT"
      [[ "$figure" == "cow" ]] && figure="default"

      if [[ "$figure" == "random" ]]; then
        local figures_arr=()
        while IFS= read -r f; do figures_arr+=("$f"); done < <(list_figures)
        figure="${figures_arr[RANDOM % ${#figures_arr[@]}]}"
      fi

      if ! figure_valid "$figure"; then
        show_error "Unknown figure '$figure' — try /animals for the full list"; continue
      fi

      local rendered; rendered=$(run_cowsay "$figure" "$text")
      local id; id=$(next_id)
      save_note "$id" "$figure" "$color" "$text" "$rendered"
      _dirty=1; continue
    fi
  done
}

# --export: render a fake board to a plain text file (no tput, no colour codes)
# Usage: bash cowboard.sh --export [output.txt]
if [[ "${1:-}" == "--export" ]]; then
  outfile="${2:-/tmp/cowboard_export.txt}"
  export_cols=${3:-120}
  export_rows=${4:-60}

  do_export() {
    local ec=$export_cols er=$export_rows
    local canvas_rows=$(( er - 6 ))

    declare -a sample_figs=( tux dragon blowfish )
    declare -a sample_cols=( default green default )
    declare -a sample_txts=( "Hello" "Hello" "Hello" )

    declare -a grid=()
    for (( r=0; r<er; r++ )); do grid[$r]=$(printf '%*s' "$ec" ''); done

    grid_write() {
      local row=$1 col=$2 str=$3
      local line="${grid[$row]}"
      local result="" i ch existing
      # pad line to needed length
      while (( ${#line} < col + ${#str} )); do line+=" "; done
      result="${line:0:$col}"
      for (( i=0; i<${#str}; i++ )); do
        ch="${str:$i:1}"
        existing="${line:$(( col + i )):1}"
        # only overwrite if existing cell is a space
        if [[ "$existing" == " " || -z "$existing" ]]; then
          result+="$ch"
        else
          result+="$existing"
        fi
      done
      result+="${line:$(( col + ${#str} ))}"
      grid[$row]="$result"
    }

    declare -a rids=() rrendered=() rwidths=() rheights=()
    for (( i=0; i<${#sample_figs[@]}; i++ )); do
      local rendered; rendered=$(moo "${sample_figs[$i]}" "${sample_txts[$i]}")
      rids+=("$i"); rrendered+=("$rendered")
      rwidths+=("$(note_width "$rendered")")
      rheights+=("$(note_height "$rendered")")
    done

    local n=${#rids[@]} GAP=2
    # Two-pass layout: first pass assigns columns and tracks max width per column
    local sorted_w=("${rwidths[@]}")
    IFS=$'\n' sorted_w=($(printf '%s\n' "${sorted_w[@]}" | sort -n)); unset IFS
    local median_w=${sorted_w[$(( n / 2 ))]}
    local num_cols=$(( ec / (median_w + GAP + 4) ))
    (( num_cols < 1 )) && num_cols=1; (( num_cols > n )) && num_cols=$n

    declare -a col_y=() col_max_w=() assign=()
    for (( c=0; c<num_cols; c++ )); do col_y[$c]=0; col_max_w[$c]=0; done
    for (( i=0; i<n; i++ )); do
      local best_col=0
      for (( c=1; c<num_cols; c++ )); do (( col_y[c] < col_y[best_col] )) && best_col=$c; done
      assign+=("$best_col")
      (( rwidths[i] > col_max_w[best_col] )) && col_max_w[$best_col]=${rwidths[i]}
      col_y[$best_col]=$(( col_y[$best_col] + rheights[i] + 1 ))
    done
    declare -a col_x=()
    col_x[0]=0
    for (( c=1; c<num_cols; c++ )); do
      col_x[$c]=$(( col_x[c-1] + col_max_w[c-1] + GAP ))
    done

    # Second pass: render into grid
    for (( c=0; c<num_cols; c++ )); do col_y[$c]=0; done
    for (( i=0; i<n; i++ )); do
      local best_col=${assign[$i]} pc=${col_x[${assign[$i]}]} pr=${col_y[${assign[$i]}]} r
      if (( pr + rheights[i] <= canvas_rows )); then
        r=$pr
        while IFS= read -r line; do
          (( r < er )) && grid_write "$r" "$pc" "$line"; (( r++ ))
        done <<< "${rrendered[$i]}"
        (( r < er )) && grid_write "$r" "$pc" "[id:${rids[$i]}]"
      fi
      col_y[${assign[$i]}]=$(( col_y[${assign[$i]}] + rheights[i] + 1 ))
    done

    local div; div=$(printf '%*s' "$ec" '' | tr ' ' '─')
    grid[$(( er - 4 ))]="$div"
    grid_write $(( er - 3 )) 2 "/tux Hello  /dragonr URGENT  /rm <id>  /clear  /list  /animals  /exit"
    grid[$(( er - 2 ))]="$div"
    grid_write $(( er - 1 )) 2 "❯"

    for (( r=0; r<er; r++ )); do printf '%s\n' "${grid[$r]}"; done
  }

  do_export > "$outfile"
  echo "Exported to $outfile (${export_cols}x${export_rows})"
  exit 0
fi

[[ "${_COWBOARD_SOURCE_ONLY:-0}" != "1" ]] && main
