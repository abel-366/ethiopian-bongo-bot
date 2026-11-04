import { useState } from 'react';
import {
  ArrowDown,
  ArrowRight,
  Check,
  ChevronRight,
  CircleHelp,
  Copy,
  LockKeyhole,
  Menu,
  Radio,
  ShieldCheck,
  Terminal,
  UsersRound,
  X,
} from 'lucide-react';

const commands = [
  { name: '/start', title: 'Meet the bot', detail: 'Open the bot in a private chat or introduce it in your group. It sends its welcome and getting-started message.' },
  { name: '/join', title: 'Take a seat', detail: 'Join the current game as a player. Send it in the game group before the host starts.' },
  { name: '/card', title: 'See your card', detail: 'Get your Bongo card for the current round. Keep it nearby as numbers are called.' },
  { name: '/players', title: 'See who’s in', detail: 'Check the current player list before the host begins.' },
  { name: '/startgame', title: 'Begin the round', detail: 'The host starts a game once everyone is ready. Agree on the start in chat first.' },
  { name: '/numbers', title: 'Review call history', detail: 'See every number called so far. The bot draws the next number automatically.' },
  { name: '/check', title: 'Check your card', detail: 'Ask the bot to check your card against the numbers called so far.' },
  { name: '/help', title: 'Get a reminder', detail: 'Show the available commands and a quick explanation in Telegram.' },
];

const setupLines = [
  { number: '01', title: 'Create your bot', text: 'In Telegram, open the verified BotFather account. Send /newbot, choose a display name and a unique username ending in bot. BotFather returns a token: treat it like a password.' },
  { number: '02', title: 'Invite it to the room', text: 'Add your bot to the group where you’ll play. Give it only the permissions it needs to respond. If it misses group messages, review Telegram’s bot privacy setting and the bot’s permissions.' },
  { number: '03', title: 'Prepare the project', text: 'On the machine that will host the bot, install the project dependencies with uv sync or pip install -r requirements.txt.' },
  { number: '04', title: 'Set the secret', text: 'Provide TELEGRAM_BOT_TOKEN to the Python process as an environment variable. Never paste it into source code, a chat, a screenshot, or a public issue.' },
  { number: '05', title: 'Start and test', text: 'Run uv run python -m bot.main, then try /start in a private chat and in your group. Keep the Python process running so the bot can call numbers.' },
];

const hostChecks = [
  'Tell the group how to join before the first round.',
  'Give everyone time to /join and review /players.',
  'Start when the room is ready; let the bot call at its steady pace.',
  'Keep the game free: no betting, buy-ins, or cash prizes.',
];

function CopyButton({ value, label = 'Copy' }: { value: string; label?: string }) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      setCopied(false);
    }
  }

  return (
    <button className="copy-button inline-flex items-center gap-2 rounded-full px-3 py-2 text-xs font-semibold text-foreground" onClick={handleCopy} type="button" data-testid={`button-copy-${value.replace(/[^a-z0-9]/gi, '')}`}>
      {copied ? <Check size={14} aria-hidden="true" /> : <Copy size={14} aria-hidden="true" />}
      {copied ? 'Copied' : label}
    </button>
  );
}

function Wordmark() {
  return (
    <a className="flex items-center gap-3" href="#top" aria-label="Bongo Bot guide, back to top">
      <span className="grid h-10 w-10 place-items-center rounded-full border border-[#ddbf91] bg-[#204d40] text-[#f2d9ab]">
        <span className="font-serif text-lg font-semibold">B</span>
      </span>
      <span className="leading-tight">
        <span className="block font-serif text-[17px] font-semibold tracking-tight">Bongo Bot</span>
        <span className="block text-[9px] font-semibold uppercase tracking-[.22em] text-[#6b746a]">Community field guide</span>
      </span>
    </a>
  );
}

function App() {
  const [menuOpen, setMenuOpen] = useState(false);
  const closeMenu = () => setMenuOpen(false);

  return (
    <div className="page-grain min-h-[100dvh] overflow-hidden bg-[#f3efe4] text-[#233a32]" id="top">
      <header className="sticky top-0 z-20 border-b border-[#dcd4c4] bg-[#f3efe4]/95 backdrop-blur-md">
        <div className="mx-auto flex h-[72px] max-w-[1240px] items-center justify-between px-5 md:px-8">
          <Wordmark />
          <nav className="hidden items-center gap-7 text-[12px] font-semibold text-[#55635a] md:flex" aria-label="Main navigation">
            <a className="hover:text-[#b9553d]" href="#setup">Setup</a>
            <a className="hover:text-[#b9553d]" href="#how-to-play">How to play</a>
            <a className="hover:text-[#b9553d]" href="#commands">Commands</a>
            <a className="hover:text-[#b9553d]" href="#deployment">Deployment</a>
          </nav>
          <a href="#setup" className="hidden items-center gap-2 rounded-full bg-[#234c3f] px-5 py-3 text-[11px] font-bold uppercase tracking-[.12em] text-[#f6f0e4] transition hover:bg-[#b9553d] sm:flex">
            Set up your bot <ArrowRight size={14} />
          </a>
          <button className="grid h-10 w-10 place-items-center rounded-full border border-[#d8cfbe] md:hidden" type="button" aria-label={menuOpen ? 'Close menu' : 'Open menu'} onClick={() => setMenuOpen(!menuOpen)} data-testid="button-mobile-menu">
            {menuOpen ? <X size={19} /> : <Menu size={19} />}
          </button>
        </div>
        {menuOpen && (
          <nav className="grid gap-1 border-t border-[#dcd4c4] bg-[#f3efe4] px-5 py-4 md:hidden" aria-label="Mobile navigation">
            {[['Setup', '#setup'], ['How to play', '#how-to-play'], ['Commands', '#commands'], ['Deployment', '#deployment']].map(([label, href]) => (
              <a key={href} onClick={closeMenu} className="rounded-lg px-3 py-3 text-sm font-semibold hover:bg-[#e9e1d1]" href={href}>{label}</a>
            ))}
          </nav>
        )}
      </header>

      <main>
        <section className="relative isolate border-b border-[#d9d0be]">
          <div className="absolute inset-0 -z-10 bg-[#21483d]" />
          <div className="hero-pattern absolute inset-y-0 right-0 -z-0 hidden w-[58%] opacity-90 md:block" />
          <div className="relative mx-auto grid min-h-[610px] max-w-[1240px] items-center gap-10 px-5 py-16 md:grid-cols-[1.02fr_.98fr] md:px-8 md:py-24">
            <div className="relative z-10 max-w-[650px]">
              <div className="reveal mb-8 inline-flex items-center gap-2 rounded-full border border-[#c8b186]/45 bg-[#f1dfba]/10 px-4 py-2 text-[10px] font-bold uppercase tracking-[.2em] text-[#e9d7b2]">
                <span className="h-1.5 w-1.5 rounded-full bg-[#d66e4e]" />
                A fair game night, together
              </div>
              <h1 className="reveal reveal-delay font-serif text-[clamp(3.4rem,8vw,7.1rem)] leading-[.93] tracking-[-.055em] text-[#f4eddd]">
                Make room<br />for <em className="font-medium text-[#e8c991]">Bongo.</em>
              </h1>
              <p className="reveal reveal-delay-2 mt-7 max-w-[510px] text-[16px] leading-7 text-[#d1d9ce] md:text-[18px]">
                A practical guide to hosting a free, welcoming Ethiopian Bongo night with an open-source Telegram bot.
              </p>
              <div className="mt-9 flex flex-wrap items-center gap-3">
                <a href="#setup" className="inline-flex items-center gap-3 rounded-full bg-[#e6c88f] px-6 py-4 text-[12px] font-bold uppercase tracking-[.11em] text-[#203d34] transition hover:-translate-y-0.5 hover:bg-[#f2d9ab]">
                  Get started <ArrowDown size={15} />
                </a>
                <a href="#commands" className="rounded-full border border-[#d6dbc9]/35 px-6 py-4 text-[12px] font-semibold text-[#f1ecdf] transition hover:bg-white/10">Browse commands</a>
              </div>
              <p className="mt-7 text-[11px] font-medium tracking-wide text-[#becbbf]">Open source · Self-hosted · Free play only</p>
            </div>

            <div className="relative z-10 mx-auto w-full max-w-[470px] md:justify-self-end">
              <div className="absolute -right-3 -top-4 h-24 w-24 rounded-full border border-[#e7c992]/35 md:-right-7 md:-top-7" />
              <div className="relative overflow-hidden rounded-[2rem] border border-[#d6c399]/30 bg-[#f1e7d1] p-6 text-[#243b32] shadow-[0_26px_70px_rgba(5,24,18,.24)] md:p-8">
                <div className="flex items-center justify-between border-b border-[#d8cdb8] pb-4">
                  <div className="flex items-center gap-3">
                    <div className="grid h-10 w-10 place-items-center rounded-full bg-[#244c40] text-[#ead5ac]"><Radio size={17} /></div>
                    <div>
                      <p className="text-[13px] font-bold">Game room</p>
                      <p className="text-[10px] text-[#6f786d]">A friendly round in progress</p>
                    </div>
                  </div>
                  <span className="rounded-full bg-[#dae3d2] px-3 py-1.5 text-[9px] font-bold uppercase tracking-[.16em] text-[#315742]">Open</span>
                </div>
                <div className="py-6">
                  <p className="text-[10px] font-bold uppercase tracking-[.18em] text-[#7b7768]">Tonight’s rhythm</p>
                  <div className="mt-4 flex items-center gap-2">
                    {['Join', 'Get card', 'Play'].map((item, i) => (
                      <div className="flex min-w-0 flex-1 items-center gap-2" key={item}>
                        <span className={`grid h-8 w-8 shrink-0 place-items-center rounded-full text-[10px] font-bold ${i < 2 ? 'bg-[#234c3f] text-[#f1e7d1]' : 'border border-[#c9bda7] text-[#59645a]'}`}>{i + 1}</span>
                        <span className="hidden text-[10px] font-semibold sm:block">{item}</span>
                        {i < 2 && <span className="h-px flex-1 bg-[#c9bda7]" />}
                      </div>
                    ))}
                  </div>
                  <div className="mt-6 rounded-2xl bg-[#e8deca] p-4">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-[10px] text-[#667268]">LAST CALL</span>
                      <span className="text-[10px] text-[#667268]">Bot draws every 12 seconds</span>
                    </div>
                    <div className="mt-3 flex items-end justify-between">
                      <span className="font-serif text-5xl leading-none tracking-tight">12</span>
                      <span className="font-mono text-[10px] text-[#657066]">/numbers</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center justify-between border-t border-[#d8cdb8] pt-4">
                  <span className="flex items-center gap-2 text-[10px] font-semibold text-[#59665c]"><span className="h-2 w-2 rounded-full bg-[#668b63]" />No stakes. Just a shared game.</span>
                  <span className="font-mono text-[9px] text-[#8b8271]">BONGO / 01</span>
                </div>
              </div>
              <div className="absolute -bottom-5 -left-3 -z-10 h-20 w-20 rounded-full border border-[#d7bd8c]/30 md:-left-8" />
            </div>
          </div>
          <div className="relative z-10 border-t border-[#d6dbc9]/20 bg-[#193e34]/60">
            <div className="mx-auto flex max-w-[1240px] flex-col gap-3 px-5 py-4 text-[10px] font-semibold uppercase tracking-[.15em] text-[#d8d8c9] sm:flex-row sm:items-center sm:justify-between md:px-8">
              <span>Built for hosts, made for the group</span>
              <span className="flex items-center gap-2 text-[#e8c991]"><ShieldCheck size={14} /> Free play only — never betting or cash prizes</span>
            </div>
          </div>
        </section>

        <section className="mx-auto grid max-w-[1240px] gap-10 px-5 py-16 md:grid-cols-[.72fr_1.28fr] md:px-8 md:py-24">
          <div>
            <p className="mb-4 text-[10px] font-bold uppercase tracking-[.22em] text-[#b9553d]">The spirit of the room</p>
            <h2 className="max-w-[380px] font-serif text-4xl leading-tight tracking-[-.035em] md:text-[3.35rem]">A good host makes space for everyone.</h2>
          </div>
          <div className="grid gap-8 sm:grid-cols-3">
            <article className="border-t border-[#c9bda9] pt-4">
              <span className="font-mono text-xs text-[#b9553d]">01 / OPEN</span>
              <h3 className="mt-4 font-serif text-xl">Easy to join</h3>
              <p className="mt-2 text-sm leading-6 text-[#68736a]">Keep the instructions visible. Give new players a moment to settle in before starting.</p>
            </article>
            <article className="border-t border-[#c9bda9] pt-4">
              <span className="font-mono text-xs text-[#b9553d]">02 / FAIR</span>
              <h3 className="mt-4 font-serif text-xl">Same shared rules</h3>
              <p className="mt-2 text-sm leading-6 text-[#68736a]">Use the bot to keep the round moving, and make the pace comfortable for the group.</p>
            </article>
            <article className="border-t border-[#c9bda9] pt-4">
              <span className="font-mono text-xs text-[#b9553d]">03 / FREE</span>
              <h3 className="mt-4 font-serif text-xl">Play for company</h3>
              <p className="mt-2 text-sm leading-6 text-[#68736a]">No money changes hands. No betting, entry fees, or cash prizes—just a game together.</p>
            </article>
          </div>
        </section>

        <section className="bg-[#e9e2d4] py-16 md:py-24" id="setup">
          <div className="mx-auto max-w-[1240px] px-5 md:px-8">
            <div className="grid gap-8 md:grid-cols-[.85fr_1.15fr]">
              <div>
                <p className="mb-4 text-[10px] font-bold uppercase tracking-[.22em] text-[#b9553d]">01 / Host setup</p>
                <h2 className="max-w-[400px] font-serif text-4xl leading-tight tracking-[-.035em] md:text-[3.3rem]">From a fresh bot to a ready room.</h2>
                <p className="mt-5 max-w-[360px] text-sm leading-6 text-[#657067]">You’ll need a Telegram account, a bot token from BotFather, and a machine that can run the project’s Python process.</p>
                <div className="mt-8 rounded-2xl border border-[#d1c6b2] bg-[#f4efe4] p-5">
                  <p className="flex items-center gap-2 text-xs font-bold"><CircleHelp size={15} className="text-[#b9553d]" />Before you begin</p>
                  <p className="mt-2 text-xs leading-5 text-[#68736a]">Use the repository README as the source of truth for its exact install command and Python entry-point filename.</p>
                </div>
              </div>
              <div className="space-y-0">
                {setupLines.map((step) => (
                  <article className="grid grid-cols-[46px_1fr] gap-4 border-t border-[#cfc5b3] py-5 md:grid-cols-[62px_1fr]" key={step.number}>
                    <span className="pt-1 font-mono text-[11px] text-[#b9553d]">{step.number}</span>
                    <div>
                      <h3 className="font-serif text-[20px]">{step.title}</h3>
                      <p className="mt-2 max-w-[590px] text-[13px] leading-6 text-[#626e64]">{step.text}</p>
                    </div>
                  </article>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="relative overflow-hidden bg-[#f3efe4] py-16 md:py-24" id="how-to-play">
          <div className="absolute -right-28 top-12 h-72 w-72 rounded-full border border-[#e0d4bd] md:right-[-50px]" />
          <div className="absolute -right-12 top-28 h-40 w-40 rounded-full border border-[#e0d4bd]" />
          <div className="relative mx-auto max-w-[1240px] px-5 md:px-8">
            <div className="flex flex-col justify-between gap-5 md:flex-row md:items-end">
              <div>
                <p className="mb-4 text-[10px] font-bold uppercase tracking-[.22em] text-[#b9553d]">02 / Round flow</p>
                <h2 className="max-w-[540px] font-serif text-4xl leading-tight tracking-[-.035em] md:text-[3.3rem]">One room. One rhythm. Start together.</h2>
              </div>
              <p className="max-w-[340px] text-sm leading-6 text-[#667268]">Keep the steps simple and the pace human. The bot handles the commands; the host keeps the room welcoming.</p>
            </div>
            <div className="mt-11 grid border-y border-[#d2c8b6] md:grid-cols-4">
              {[
                { n: '01', command: '/start', title: 'Open the door', text: 'Have people start the bot, then add it to the group where the game will happen.' },
                { n: '02', command: '/join', title: 'Gather players', text: 'Players join from the group. Check the room with /players before the round.' },
                { n: '03', command: '/card', title: 'Get ready', text: 'Each player asks for their card and keeps it handy for the round.' },
                { n: '04', command: '/startgame', title: 'Begin the game', text: 'When everyone is ready, a group administrator starts. The bot then calls numbers automatically.' },
              ].map((step, index) => (
                <article className={`relative border-b border-[#d2c8b6] py-6 md:border-b-0 md:py-8 ${index > 0 ? 'md:border-l md:pl-6' : ''} ${index < 3 ? 'md:pr-6' : ''}`} key={step.n}>
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[10px] text-[#b9553d]">{step.n} / 04</span>
                    <span className="font-mono text-[10px] text-[#617067]">{step.command}</span>
                  </div>
                  <h3 className="mt-8 font-serif text-[22px]">{step.title}</h3>
                  <p className="mt-2 text-[13px] leading-6 text-[#69746b]">{step.text}</p>
                </article>
              ))}
            </div>
            <div className="mt-6 flex flex-col gap-4 rounded-2xl bg-[#234b3f] px-6 py-5 text-[#f3eddf] sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-start gap-3">
                <UsersRound size={18} className="mt-0.5 shrink-0 text-[#e6c88f]" />
                <p className="text-[13px] leading-6"><strong className="font-semibold">During the round:</strong> the bot calls one number every 12 seconds and checks every card. Players can use /numbers to review calls and /check to verify their card.</p>
              </div>
              <a className="inline-flex shrink-0 items-center gap-2 text-[11px] font-bold uppercase tracking-[.12em] text-[#e6c88f] hover:text-white" href="#commands">See every command <ChevronRight size={15} /></a>
            </div>
          </div>
        </section>

        <section className="bg-[#21483d] py-16 text-[#f4eddd] md:py-24" id="commands">
          <div className="mx-auto max-w-[1240px] px-5 md:px-8">
            <div className="flex flex-col justify-between gap-6 md:flex-row md:items-end">
              <div>
                <p className="mb-4 text-[10px] font-bold uppercase tracking-[.22em] text-[#e5c78f]">03 / Command index</p>
                <h2 className="font-serif text-4xl leading-tight tracking-[-.035em] md:text-[3.3rem]">Eight commands. The whole table.</h2>
              </div>
              <p className="max-w-[320px] text-sm leading-6 text-[#c6d1c5]">Send these in the game group unless your bot’s own help message says otherwise. Start with /help if you need a reminder.</p>
            </div>
            <div className="mt-10 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {commands.map((command, index) => (
                <article className="command-card flex min-h-[210px] flex-col rounded-2xl border border-[#638073]/45 bg-[#294f44] p-5" key={command.name} data-testid={`card-command-${command.name.slice(1)}`}>
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[10px] text-[#d8c294]">0{index + 1} / CMD</span>
                    <CopyButton value={command.name} label="Copy" />
                  </div>
                  <p className="mt-5 font-mono text-[19px] tracking-tight text-[#f1d6a5]">{command.name}</p>
                  <h3 className="mt-2 font-serif text-[19px]">{command.title}</h3>
                  <p className="mt-2 text-[12px] leading-5 text-[#cfdbd0]">{command.detail}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="bg-[#e9e2d4] py-16 md:py-24" id="security">
          <div className="mx-auto grid max-w-[1240px] gap-10 px-5 md:grid-cols-[.78fr_1.22fr] md:px-8">
            <div>
              <p className="mb-4 text-[10px] font-bold uppercase tracking-[.22em] text-[#b9553d]">04 / Keep the key safe</p>
              <h2 className="max-w-[420px] font-serif text-4xl leading-tight tracking-[-.035em] md:text-[3.2rem]">Your token opens the bot. Keep it yours.</h2>
              <p className="mt-5 max-w-[390px] text-sm leading-6 text-[#657067]">Anyone with the token may be able to control your bot. Protect it like a credential, not a configuration example.</p>
            </div>
            <div className="overflow-hidden rounded-[1.5rem] bg-[#1c3932] text-[#f1ead9]">
              <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
                <div className="flex items-center gap-2 text-[11px] font-semibold"><Terminal size={15} className="text-[#e7c891]" /> Local shell</div>
                <span className="font-mono text-[9px] uppercase tracking-[.16em] text-[#9eafa1]">Example only</span>
              </div>
              <div className="space-y-4 px-5 py-6 md:px-7">
                <p className="text-[12px] leading-5 text-[#bdc9be]">Set it in the environment used to launch the process. Don’t commit a real token or a filled-in .env file.</p>
                <div className="overflow-x-auto rounded-xl border border-white/10 bg-[#142d27] p-4">
                  <code className="whitespace-nowrap font-mono text-[12px] text-[#f2d7a6]">export TELEGRAM_BOT_TOKEN=&quot;paste-your-token-here&quot;</code>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <CopyButton value={'export TELEGRAM_BOT_TOKEN="paste-your-token-here"'} label="Copy example" />
                  <span className="text-[10px] text-[#9fb0a2]">Replace the placeholder privately on the host machine.</span>
                </div>
              </div>
              <div className="grid gap-0 border-t border-white/10 sm:grid-cols-3">
                {[
                  ['Never commit', 'Keep tokens out of Git history and shared snippets.'],
                  ['Limit access', 'Restrict who can read the service environment.'],
                  ['Rotate quickly', 'If exposed, revoke it with BotFather and update the host.'],
                ].map(([title, text]) => (
                  <div className="border-b border-white/10 px-5 py-4 last:border-b-0 sm:border-b-0 sm:border-r sm:last:border-r-0" key={title}>
                    <p className="flex items-center gap-2 text-[11px] font-bold"><LockKeyhole size={13} className="text-[#e7c891]" />{title}</p>
                    <p className="mt-2 text-[10px] leading-5 text-[#b8c6b9]">{text}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="bg-[#f3efe4] py-16 md:py-24" id="deployment">
          <div className="mx-auto max-w-[1240px] px-5 md:px-8">
            <div className="grid gap-8 md:grid-cols-[.8fr_1.2fr]">
              <div>
                <p className="mb-4 text-[10px] font-bold uppercase tracking-[.22em] text-[#b9553d]">05 / Keep it running</p>
                <h2 className="max-w-[410px] font-serif text-4xl leading-tight tracking-[-.035em] md:text-[3.2rem]">Telegram needs a public HTTPS endpoint.</h2>
                <p className="mt-5 max-w-[390px] text-sm leading-6 text-[#657067]">The FastAPI service receives Telegram updates through a webhook and registers its public URL when it starts.</p>
                <div className="mt-7 flex items-start gap-3 border-l-2 border-[#bb6248] pl-4">
                  <Radio size={16} className="mt-1 shrink-0 text-[#b9553d]" />
                  <p className="text-xs leading-5 text-[#626e64]"><strong className="text-[#263d33]">Use one update method per token.</strong> Do not run long polling alongside the configured webhook.</p>
                </div>
              </div>
              <div className="space-y-3">
                <article className="rounded-2xl border border-[#d4cbb9] bg-[#eee8da] p-5 md:p-6">
                  <div className="flex items-center gap-3">
                    <span className="grid h-9 w-9 place-items-center rounded-full bg-[#d7e0d2] font-mono text-xs font-bold text-[#355342]">A</span>
                    <div><h3 className="font-serif text-xl">Run the webhook server</h3><p className="text-[10px] text-[#768075]">Render starts Uvicorn on its assigned port</p></div>
                  </div>
                  <p className="mt-4 text-[12px] leading-5 text-[#657067]">Deploy this repository as a Render Web Service. Store TELEGRAM_BOT_TOKEN and TELEGRAM_WEBHOOK_SECRET in Render’s environment settings.</p>
                  <div className="mt-4 rounded-xl bg-[#233c33] px-4 py-3 font-mono text-[11px] text-[#e7c891]">uvicorn bot.web:app --host 0.0.0.0 --port $PORT</div>
                </article>
                <article className="rounded-2xl border border-[#d4cbb9] bg-[#eee8da] p-5 md:p-6">
                  <div className="flex items-center gap-3">
                    <span className="grid h-9 w-9 place-items-center rounded-full bg-[#f1dbc7] font-mono text-xs font-bold text-[#9b523a]">B</span>
                    <div><h3 className="font-serif text-xl">Know the free-tier limits</h3><p className="text-[10px] text-[#768075]">Cold starts and temporary game data</p></div>
                  </div>
                  <p className="mt-4 text-[12px] leading-5 text-[#657067]">Render’s free service can sleep after inactivity, and its local SQLite file is lost on sleep or redeploy. Use an always-on plan and persistent storage for uninterrupted rounds.</p>
                </article>
                <div className="rounded-xl border border-dashed border-[#c6baa5] px-5 py-4">
                  <p className="text-[11px] font-bold">Before you publish</p>
                  <p className="mt-1 text-[11px] leading-5 text-[#68736a]">Publishing this web guide does not run the bot. Deploy the FastAPI service separately, and do not run polling and webhook modes at the same time.</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="bg-[#e4d7bc] py-14 md:py-20">
          <div className="mx-auto grid max-w-[1240px] gap-10 px-5 md:grid-cols-[.72fr_1.28fr] md:px-8">
            <div>
              <p className="mb-4 text-[10px] font-bold uppercase tracking-[.22em] text-[#a84e39]">06 / Good hosting</p>
              <h2 className="max-w-[370px] font-serif text-4xl leading-tight tracking-[-.035em]">The best round is one people want to return to.</h2>
            </div>
            <div className="grid gap-x-8 sm:grid-cols-2">
              {hostChecks.map((check, index) => (
                <div className="flex gap-3 border-t border-[#c8b99e] py-4" key={check}>
                  <span className="font-mono text-[10px] text-[#a84e39]">0{index + 1}</span>
                  <p className="text-[13px] leading-5 text-[#41564a]">{check}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="bg-[#1d4036] px-5 py-14 text-[#f3eddf] md:px-8 md:py-20">
          <div className="mx-auto flex max-w-[1240px] flex-col justify-between gap-8 md:flex-row md:items-center">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-[.22em] text-[#e7c891]">Ready when the room is</p>
              <h2 className="mt-3 max-w-[600px] font-serif text-3xl leading-tight tracking-[-.025em] md:text-[2.7rem]">Set the table. Invite your people. Keep it free.</h2>
            </div>
            <div className="flex flex-wrap gap-3">
              <a href="#setup" className="inline-flex items-center gap-2 rounded-full bg-[#e6c88f] px-5 py-3 text-[11px] font-bold uppercase tracking-[.1em] text-[#203d34] hover:bg-[#f2d9ab]">Back to setup <ArrowRight size={14} /></a>
              <a href="#commands" className="inline-flex items-center gap-2 rounded-full border border-white/25 px-5 py-3 text-[11px] font-semibold text-[#f3eddf] hover:bg-white/10">Command index <ChevronRight size={14} /></a>
            </div>
          </div>
        </section>
      </main>

      <footer className="bg-[#17372f] text-[#c5d0c3]">
        <div className="mx-auto flex max-w-[1240px] flex-col gap-5 px-5 py-7 text-[10px] md:flex-row md:items-center md:justify-between md:px-8">
          <div className="flex items-center gap-3">
            <span className="grid h-8 w-8 place-items-center rounded-full border border-[#bda87c]/50 font-serif text-sm text-[#e6c88f]">B</span>
            <span><strong className="font-semibold text-[#f0eadc]">Bongo Bot</strong><span className="mx-2 text-[#72877a]">/</span>Community field guide</span>
          </div>
          <p className="max-w-[520px] leading-5 md:text-right">Open-source community play. No betting, entry fees, or cash prizes. Follow the project README and Telegram’s current bot guidance for implementation specifics.</p>
        </div>
        <div className="h-1 bg-[#b9553d]" />
      </footer>
    </div>
  );
}

export default App;
