#!/usr/bin/env bash
# cowboard — sticky note board in the terminal
# Zero dependencies (no cowsay, no jq, no Python)
# Commands: /<figure>[g|r|b|y] <text>  /rm <id>  /clear  /list  /animals  /colors  /q

set -o pipefail

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

# make_sticky <text> <wrap_width>
# Renders a sticky note with a curled top-right corner. No animal.
make_sticky() {
  local text="$1"
  # Wrap width: sqrt(len * 2) gives a roughly square note (factor 2 for terminal char aspect).
  # Clamp between the longest single word and 40.
  local len=${#text}
  local wrap; wrap=$(( len > 0 ? $(echo "scale=0; sqrt($len * 4) / 1" | bc) : 4 ))
  (( wrap > 40 )) && wrap=40

  # word-wrap
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

  # max = longest line (no minimum — fit to content)
  local max=0
  for l in "${lines[@]}"; do (( ${#l} > max )) && max=${#l}; done

  local curl=2
  local inner=$(( max + 2 ))

  # top border with curl
  printf '+'
  printf '%*s' $(( inner - curl )) '' | tr ' ' '-'
  printf '%s+\n' '\\'

  # curl row
  printf '|'
  printf '%*s' $(( inner - curl )) ''
  printf ' \\'
  printf '\n'

  # text rows
  for l in "${lines[@]}"; do
    printf '| %-*s |\n' "$max" "$l"
  done

  # bottom border
  printf '+'
  printf '%*s' "$inner" '' | tr ' ' '-'
  printf '+\n'
}

# moo <figure> <text>
# Full cowsay equivalent: bubble + animal (or sticky note for default/cow)
moo() {
  local figure="$1"
  local text="$2"
  local wrap="${3:-40}"

  if [[ "$figure" == "sticky" || "$figure" == "note" ]]; then
    make_sticky "$text"
    return
  fi

  local bubble
  bubble=$(make_bubble "$text" "$wrap")
  local animal
  animal=$(get_animal "$figure")
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
  [[ "$1" == "sticky" || "$1" == "note" ]] && return 0
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
  local stem="${figure_part%?}"
  # Only treat last char as color suffix if the stem is a valid figure name
  case "$last" in
    g|r|b|y)
      if [[ -n "$stem" ]] && figure_valid "$stem"; then
        case "$last" in
          g) PARSE_COLOR="green"  ;;
          r) PARSE_COLOR="red"    ;;
          b) PARSE_COLOR="blue"   ;;
          y) PARSE_COLOR="yellow" ;;
        esac
        PARSE_FIGURE="$stem"
      else
        PARSE_COLOR="default"; PARSE_FIGURE="$figure_part"
      fi ;;
    *) PARSE_COLOR="default"; PARSE_FIGURE="$figure_part" ;;
  esac
  [[ -z "$PARSE_FIGURE" ]] && return 1
  return 0
}

# ── display ───────────────────────────────────────────────────────────────────

_last_cols=0
_last_rows=0
_last_note_sig="FORCE"

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

# _try_layout <cols> <canvas_rows>
# Attempts masonry layout with current _wids/_hgts/_rnds arrays.
# Writes results into _asgn[], _cx[], _cy_result[], _fits[].
# Returns 1 if any note didn't fit, 0 if all fit.
_try_layout() {
  local cols="$1" canvas_rows="$2" GAP=2
  (( canvas_rows < 1 )) && { _fits=(); local i; for (( i=0; i<${#_ids[@]}; i++ )); do _fits+=(0); done; return 1; }
  local n=${#_ids[@]}

  # Median width for column count estimate
  local sorted_w=("${_wids[@]}")
  IFS=$'\n' sorted_w=($(printf '%s\n' "${sorted_w[@]}" | sort -n)); unset IFS
  local median_w=${sorted_w[$(( n / 2 ))]}
  local num_cols=$(( cols / (median_w + GAP + 4) ))
  (( num_cols < 1 )) && num_cols=1
  (( num_cols > n )) && num_cols=$n

  # Sort notes tallest-first for better bin-packing; _order maps sorted→original index
  local _order=()
  local _order_tmp
  _order_tmp=$(for (( i=0; i<n; i++ )); do printf '%s %s\n' "${_hgts[$i]}" "$i"; done | sort -rn | awk '{print $2}')
  while IFS= read -r idx; do _order+=("$idx"); done <<< "$_order_tmp"

  local col_y=() col_max_w=()
  for (( c=0; c<num_cols; c++ )); do col_y[$c]=0; col_max_w[$c]=0; done

  # Pass A: assign to shortest column (tallest notes first)
  _asgn=()
  for (( i=0; i<n; i++ )); do _asgn+=(-1); done  # init
  for (( si=0; si<n; si++ )); do
    local i=${_order[$si]}
    local best=0
    for (( c=1; c<num_cols; c++ )); do (( col_y[c] < col_y[best] )) && best=$c; done
    _asgn[$i]=$best
    (( _wids[i] > col_max_w[best] )) && col_max_w[$best]=${_wids[i]}
    col_y[$best]=$(( col_y[$best] + _hgts[i] + 1 ))
  done

  # Reduce num_cols until the layout fits horizontally, then redo assignment
  local prev_num_cols=$(( num_cols + 1 ))
  while (( num_cols != prev_num_cols )); do
    prev_num_cols=$num_cols

    # Recompute col_x for current num_cols
    _cx=()
    _cx[0]=0
    for (( c=1; c<num_cols; c++ )); do
      _cx[$c]=$(( _cx[c-1] + col_max_w[c-1] + GAP ))
    done

    # If it fits, done
    if (( _cx[num_cols-1] + col_max_w[num_cols-1] <= cols )); then
      break
    fi

    # Doesn't fit — reduce and redo full assignment with fewer columns
    (( num_cols > 1 )) && (( num_cols-- )) || break
    for (( c=0; c<num_cols; c++ )); do col_y[$c]=0; col_max_w[$c]=0; done
    _asgn=()
    for (( i=0; i<n; i++ )); do _asgn+=(-1); done
    for (( si=0; si<n; si++ )); do
      local i=${_order[$si]}
      local best=0
      for (( c=1; c<num_cols; c++ )); do (( col_y[c] < col_y[best] )) && best=$c; done
      _asgn[$i]=$best
      (( _wids[i] > col_max_w[best] )) && col_max_w[$best]=${_wids[i]}
      col_y[$best]=$(( col_y[$best] + _hgts[i] + 1 ))
    done
  done

  # Pass B: place each note and check if it fits
  for (( c=0; c<num_cols; c++ )); do col_y[$c]=0; done
  _cy_result=(); _fits=()
  local all_fit=0
  for (( i=0; i<n; i++ )); do
    local bc=${_asgn[$i]} pr pc
    pr=${col_y[$bc]}
    pc=${_cx[$bc]}
    _cy_result+=("$pr")
    if (( pr + _hgts[i] <= canvas_rows && pc + _wids[i] <= cols )); then
      _fits+=(1)
    else
      _fits+=(0)
      all_fit=1
    fi
    col_y[$bc]=$(( col_y[$bc] + _hgts[i] + 1 ))
  done
  return $all_fit
}

compute_layout() {
  local cols="$1" canvas_rows="$2"
  L_ids=(); L_colors=(); L_rendereds=(); L_rows=(); L_cols=(); L_widths=(); L_heights=()

  [[ ! -s "$PERSIST" ]] && return

  # Load all notes — keep full animal rendering and sticky fallback separately
  local _ids=() _colors=() _texts=()
  local _full_rnds=() _full_wids=() _full_hgts=()
  local _stky_rnds=() _stky_wids=() _stky_hgts=()
  local _use_sticky=()   # 0=full, 1=sticky

  while IFS=$'\t' read -r nid nfigure ncolor ntext nrendered; do
    local rendered; rendered=$(decode "$nrendered")
    local text; text=$(decode "$ntext")
    local sticky; sticky=$(make_sticky "$text")
    _ids+=("$nid"); _colors+=("$ncolor"); _texts+=("$text")
    _full_rnds+=("$rendered")
    _full_wids+=("$(note_width "$rendered")")
    _full_hgts+=("$(note_height "$rendered")")
    _stky_rnds+=("$sticky")
    _stky_wids+=("$(note_width "$sticky")")
    _stky_hgts+=("$(note_height "$sticky")")
    _use_sticky+=(0)
  done < "$PERSIST"

  local n=${#_ids[@]}
  (( n == 0 )) && return

  # Working arrays for layout attempts
  local _wids=() _hgts=() _rnds=()
  local _asgn=() _cx=() _cy_result=() _fits=()

  # Iteratively substitute the largest non-sticky note until everything fits
  local max_iters=$(( n + 1 )) iter=0
  while (( iter <= max_iters )); do
    # Build working arrays from current sticky flags
    _wids=(); _hgts=(); _rnds=()
    for (( i=0; i<n; i++ )); do
      if (( _use_sticky[i] )); then
        _wids+=("${_stky_wids[$i]}"); _hgts+=("${_stky_hgts[$i]}"); _rnds+=("${_stky_rnds[$i]}")
      else
        _wids+=("${_full_wids[$i]}"); _hgts+=("${_full_hgts[$i]}"); _rnds+=("${_full_rnds[$i]}")
      fi
    done

    _try_layout "$cols" "$canvas_rows" && break  # all fit

    # Find the largest full-size note to substitute to sticky.
    # Prefer notes that didn't fit; if all non-fitting are already sticky,
    # pick the largest *fitting* full note (it may be causing column bloat).
    local worst=-1 worst_area=0
    for (( i=0; i<n; i++ )); do
      if (( _fits[i] == 0 && _use_sticky[i] == 0 )); then
        local area=$(( _full_wids[i] * _full_hgts[i] ))
        if (( area > worst_area )); then worst_area=$area; worst=$i; fi
      fi
    done
    if (( worst == -1 )); then
      # No non-fitting full notes — try shrinking the largest fitting full note
      # in case it is bloating a column and preventing others from fitting
      for (( i=0; i<n; i++ )); do
        if (( _use_sticky[i] == 0 )); then
          local area=$(( _full_wids[i] * _full_hgts[i] ))
          if (( area > worst_area )); then worst_area=$area; worst=$i; fi
        fi
      done
    fi
    if (( worst == -1 )); then
      # Everything is already sticky; final layout pass and done
      _try_layout "$cols" "$canvas_rows"
      break
    fi
    _use_sticky[$worst]=1
    (( iter++ ))
  done

  # Rebuild working arrays one last time so _wids/_hgts/_rnds match final flags
  _wids=(); _hgts=(); _rnds=()
  for (( i=0; i<n; i++ )); do
    if (( _use_sticky[i] )); then
      _wids+=("${_stky_wids[$i]}"); _hgts+=("${_stky_hgts[$i]}"); _rnds+=("${_stky_rnds[$i]}")
    else
      _wids+=("${_full_wids[$i]}"); _hgts+=("${_full_hgts[$i]}"); _rnds+=("${_full_rnds[$i]}")
    fi
  done
  # Run a final authoritative layout so _fits[], _asgn[], _cx[], _cy_result[]
  # are fully consistent with the current _wids/_hgts
  _try_layout "$cols" "$canvas_rows"

  # Emit final layout
  for (( i=0; i<n; i++ )); do
    local bc=${_asgn[$i]} pr=${_cy_result[$i]} pc=${_cx[${_asgn[$i]}]}
    if (( _fits[i] )); then
      L_ids+=("${_ids[$i]}"); L_colors+=("${_colors[$i]}")
      L_rendereds+=("${_rnds[$i]}")
      L_rows+=("$pr"); L_cols+=("$pc")
      L_widths+=("${_wids[$i]}"); L_heights+=("${_hgts[$i]}")
    fi
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
  (( cols < 10 || rows < 8 )) && return  # terminal too small to do anything useful
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

# Global picker state (no nested functions / local -a on bash 3.2)
_PICK_ANIMALS=()
_PICK_N=0
_PICK_NCOLS=0
_PICK_CELL_W=0
_PICK_ROWS=0
_PICK_RESULT=""

_picker_draw_full() {
  local sel=$1 i r c
  clear
  tput cup 0 2; printf "\033[1mPick an animal\033[0m  (arrows  Enter=select  Esc=cancel)"
  for (( i=0; i<_PICK_N; i++ )); do
    r=$(( 1 + i / _PICK_NCOLS ))
    c=$(( (i % _PICK_NCOLS) * _PICK_CELL_W ))
    tput cup "$r" "$c"
    if (( i == sel )); then
      printf "\033[7m %-*s \033[0m" $(( _PICK_CELL_W - 2 )) "${_PICK_ANIMALS[$i]}"
    else
      printf " %-*s " $(( _PICK_CELL_W - 2 )) "${_PICK_ANIMALS[$i]}"
    fi
  done
  draw_bar "$_PICK_ROWS"
}

# Redraw only the two cells that changed — no flicker
_picker_move() {
  local old_sel=$1 new_sel=$2 r c
  # deselect old
  r=$(( 1 + old_sel / _PICK_NCOLS ))
  c=$(( (old_sel % _PICK_NCOLS) * _PICK_CELL_W ))
  tput cup "$r" "$c"
  printf " %-*s " $(( _PICK_CELL_W - 2 )) "${_PICK_ANIMALS[$old_sel]}"
  # select new
  r=$(( 1 + new_sel / _PICK_NCOLS ))
  c=$(( (new_sel % _PICK_NCOLS) * _PICK_CELL_W ))
  tput cup "$r" "$c"
  printf "\033[7m %-*s \033[0m" $(( _PICK_CELL_W - 2 )) "${_PICK_ANIMALS[$new_sel]}"
}

pick_animal() {
  # Returns the chosen figure name on stdout, or empty string if cancelled.
  _PICK_ANIMALS=()
  while IFS= read -r f; do _PICK_ANIMALS+=("$f"); done < <(list_figures)
  _PICK_N=${#_PICK_ANIMALS[@]}

  local cols
  cols=$(tput cols); _PICK_ROWS=$(tput lines)

  local max_w=0 f
  for f in "${_PICK_ANIMALS[@]}"; do (( ${#f} > max_w )) && max_w=${#f}; done
  _PICK_CELL_W=$(( max_w + 3 ))
  _PICK_NCOLS=$(( cols / _PICK_CELL_W ))
  (( _PICK_NCOLS < 1 )) && _PICK_NCOLS=1

  local sel=0
  _picker_draw_full "$sel"
  tput civis

  local result="" key b1 b2 new_sel
  while true; do
    IFS= read -r -s -n1 key
    # Arrow keys arrive as 3 bytes: ESC [ A/B/C/D
    if [[ "$key" == $'\x1b' ]]; then
      IFS= read -r -s -n1 -t 1 b1
      IFS= read -r -s -n1 -t 1 b2
      if [[ "$b1" == "[" ]]; then
        new_sel=$sel
        case "$b2" in
          A) if (( sel >= _PICK_NCOLS )); then (( new_sel = sel - _PICK_NCOLS )); fi ;;
          B) if (( sel + _PICK_NCOLS < _PICK_N )); then (( new_sel = sel + _PICK_NCOLS )); fi ;;
          C) if (( sel + 1 < _PICK_N )); then (( new_sel = sel + 1 )); fi ;;
          D) if (( sel > 0 )); then (( new_sel = sel - 1 )); fi ;;
        esac
        if (( new_sel != sel )); then
          _picker_move "$sel" "$new_sel"
          sel=$new_sel
        fi
      else
        result=""; break
      fi
    elif [[ "$key" == "" || "$key" == $'\n' || "$key" == $'\r' ]]; then
      result="${_PICK_ANIMALS[$sel]}"; break
    elif [[ "$key" == "q" || "$key" == $'\x03' ]]; then
      result=""; break
    fi
  done

  tput cnorm
  _PICK_RESULT="$result"
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

  bind 'set bell-style none' 2>/dev/null || true

  trap '_cowboard_resized=1; _last_note_sig="FORCE"; redraw; _trap_r=$(tput lines); tput cup $(( _trap_r - 3 )) 0; tput el; printf "❯ "' SIGWINCH
  trap 'history -w "$HISTFILE"' EXIT

  local _cowboard_resized=0
  while true; do
    if (( _dirty )); then redraw; _dirty=0; fi

    _cowboard_resized=0
    local rows; rows=$(tput lines)
    tput cup $(( rows - 3 )) 0; tput el
    IFS= read -e -r -p "❯ " input || { (( _cowboard_resized )) && continue; echo ""; break; }
    [[ -n "$input" ]] && history -s "$input"

    input="${input#"${input%%[![:space:]]*}"}"
    input="${input%"${input##*[![:space:]]}"}"
    [[ -z "$input" ]] && continue

    # clear any previous error on new command
    clear_error

    if [[ "$input" == "/q" || "$input" == "/quit" || "$input" == "/exit" ]]; then clear; break; fi

    if [[ "$input" == "/?" || "$input" == "/help" ]]; then
      clear
      printf '\n'
      printf '  \033[1mcowboard — commands\033[0m\n\n'
      printf '  \033[1m/<figure> <text>\033[0m        add a note  (e.g. /tux Hello)\n'
      printf '  \033[1m/<figure>[g|r|b|y] <text>\033[0m  add a coloured note  (e.g. /dragonr URGENT)\n'
      printf '  \033[1m/cow <text>\033[0m             add a default cow note\n'
      printf '  \033[1m/random <text>\033[0m          random figure\n'
      printf '  \033[1m<text>\033[0m                  plain text → default cow note\n\n'
      printf '  \033[1m/animals\033[0m                interactive animal picker\n'
      printf '  \033[1m/colors\033[0m                 list available colours\n'
      printf '  \033[1m/list\033[0m                   list all notes with ids\n'
      printf '  \033[1m/rm <id>\033[0m                remove a note by id\n'
      printf '  \033[1m/clear\033[0m                  remove all notes (with confirmation)\n\n'
      printf '  \033[1m/? /help\033[0m                show this help\n'
      printf '  \033[1m/q /exit\033[0m                quit\n\n'
      printf '  \033[2m↑↓ arrow keys browse command history\033[0m\n\n'
      read -r -p "  Press enter to continue..." _; _last_note_sig="FORCE"; _dirty=1; continue
    fi

    if [[ "$input" == "/list" ]]; then
      cmd_list; read -r -p "  Press enter to continue..." _; _last_note_sig="FORCE"; _dirty=1; continue
    fi

    if [[ "$input" == "/colors" ]]; then
      echo ""
      printf "  $(color_code green)g  green${COLOR_RESET}\n"
      printf "  $(color_code red)r  red${COLOR_RESET}\n"
      printf "  $(color_code blue)b  blue${COLOR_RESET}\n"
      printf "  $(color_code yellow)y  yellow${COLOR_RESET}\n"
      printf "  $(color_code default)(none)  default${COLOR_RESET}\n"
      echo ""
      read -r -p "  Press enter to continue..." _; _last_note_sig="FORCE"; _dirty=1; continue
    fi

    if [[ "$input" == "/animals" ]]; then
      _PICK_RESULT=""
      pick_animal
      local picked="$_PICK_RESULT"
      _dirty=1
      if [[ -n "$picked" ]]; then
        # Restore board, then prompt with /<animal> pre-typed; user adds text + Enter
        _last_note_sig="FORCE"; redraw; _dirty=0
        local rows; rows=$(tput lines)
        tput cup $(( rows - 3 )) 0; tput el
        IFS= read -e -r -p "❯ /$picked" rest
        input="/$picked$rest"
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
        remove_note "$rm_id"; _last_note_sig="FORCE"; _dirty=1
      else
        show_error "No note with id $rm_id"
      fi
      continue
    fi

    if [[ "$input" == "/clear" ]]; then
      local rows2; rows2=$(tput lines)
      tput cup $(( rows2 - 3 )) 0; tput el
      printf "  Remove ALL notes? [y/N] "
      local confirm=""
      IFS= read -r -s -n1 confirm
      if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
        clear_all_notes; _last_note_sig="FORCE"; _dirty=1
      else
        _last_note_sig="FORCE"; _dirty=1
      fi
      continue
    fi

    # plain text → sticky note; optional color prefix: g/r/b/y <text>
    if [[ "$input" != /* ]]; then
      local _first="${input%% *}" _rest="${input#* }"
      if [[ "${#_first}" == "1" && "$_first" =~ ^[grby]$ && "$_rest" != "$input" ]]; then
        input="/sticky${_first} $_rest"
      else
        input="/sticky $input"
      fi
    fi

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
