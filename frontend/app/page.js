import Link from 'next/link'

const suites = [
  {
    name: 'Suíte Real',
    description: 'Explore o auge do luxo em nossa Suíte Real. Projetada para momentos inesquecíveis, esta acomodação oferece uma banheira privativa, acabamentos em mármore Carrara e, como cortesia, uma garrafa de champagne para celebrar sua estadia. É o cenário perfeito para uma escapada romântica ou uma celebração especial.',
    details: [
      'Tamanho Médio: 60m²',
      'Ocupação Máxima: 2 pessoas',
      'Cama: King',
      'Ar-condicionado: 1',
      'Wi-Fi',
      'TV de tela plana: 1',
      'Banheiro privativo e amplo: 1',
      'Frigobar: 1',
      'Banheira: 1'
    ],
    image: '/images/suites/suite-real.png',
    featured: true,
  },
  {
    name: 'Suite Luxo',
    description: 'A Suíte Luxo combina conforto e sofisticação em um espaço generoso. Ideal para quem busca uma estadia relaxante, ela é equipada com cama queen, ar-condicionado e frigobar. Algumas unidades selecionadas oferecem uma varanda privativa, perfeita para apreciar a brisa de Cabo Frio.',
    details: [
      'Tamanho Médio: 29m²',
      'Ocupação Máxima: 2 a 3 Pessoas',
      'Cama: Queen',
      'Ar-condicionado: 1',
      'Wi-Fi',
      'TV de tela plana: 1',
      'Banheiro privativo amplo: 1',
      'Varanda (em algumas unidades)',
      'Frigobar'
    ],
    image: '/images/suites/suite-luxo.png',
  },
  {
    name: 'Suite Dupla',
    description: 'Ideal para famílias ou pequenos grupos, nossa Suíte Dupla oferece conforto e praticidade em um ambiente acolhedor e bem equipado. Com capacidade para até 4 pessoas, conta com duas camas espaçosas, ar-condicionado, Wi-Fi, TV e banheiro privativo. O espaço é cuidadosamente preparado para garantir uma estadia tranquila, com comodidades que atendem tanto a quem viaja a lazer quanto a trabalho. Conforto e funcionalidade em perfeita harmonia para sua melhor experiência.',
    details: [
      'Tamanho Médio: 60m²',
      'Ocupação Máxima: 4 a 5 pessoas',
      'Cama: Queen',
      'Ar-condicionado: 2',
      'Wi-Fi',
      'TV de tela plana: 2',
      'Banheiros privativos: 2',
      'Frigobar: 2',
      'Varandas: 2',
      'Portas: 2'
    ],
    image: '/images/suites/suite-dupla.png',
  },
  {
    name: 'Suite Master',
    description: 'Nossa Suíte Master é a definição de exclusividade. Sendo a opção mais ampla e completa do hotel, ela foi desenhada para estadias especiais, oferecendo uma cama king size, varanda privativa e um banheiro espaçoso. Desfrute do máximo de conforto e privacidade.',
    details: [
      'Tamanho Médio: 60m²',
      'Ocupação Máxima: 2 Pessoas',
      'Cama: King',
      'Ar-condicionado: 1',
      'Wi-Fi',
      'TV de tela plana: 1',
      'Banheiro amplo e privativo: 1',
      'Varanda: 1',
      'Frigobar: 1'
    ],
    image: '/images/suites/suite-master.png',
  },
]

const testimonials = [
  {
    name: 'Rosangela',
    quote: 'Chegamos à noite sem reserva, cidade lotada, já havia passado por outros hotéis e estavam completos, mas mesmo assim, fomos muito bem recepcionados.',
  },
  {
    name: 'Cristina Barracho',
    quote: 'Quarto arejado, limpo e bem claro, amplo e com ar-condicionado, sacada com mesinha e banco. Café da manhã muito bem servido, maravilhoso. Pessoal muito atencioso. Nota 1000! Diferenciais: fica de frente para o mercado Extra, a 800 metros da Praia do Forte, rodoviária pertinho e vários restaurantes e burguerias próximas. Super recomendo!',
  },
  {
    name: 'Oswaldo Santos',
    quote: 'Os serviços de quarto são excelentes, hotel completamente limpo, os funcionários são bem educados — na minha opinião, isso é um fator muito importante. O hotel está bem localizado, próximo a supermercados e restaurantes. Eu gostei muito e super indico.',
  },
  {
    name: 'Silvana Lira',
    quote: 'Com ótima localização: próximo a supermercado, farmácia, bares, restaurantes e a menos de 5 minutos das belas praias. O hotel dispõe de apartamentos amplos (destaque para a suíte Real, que é um luxo), confortáveis, bem decorados, auditório, serviço de bar, restaurante, além da cordialidade e simpatia dos funcionários. Sem dúvida, é uma excelente escolha pra quem for a Cabo Frio-RJ a passeio ou a negócios.',
  },
  {
    name: 'Monique Alvares',
    quote: 'Hotel muito limpo, bem localizado, próximo ao mercado e à praia. Excelente atendimento e café da manhã muito bom.',
  },
]

const benefits = [
  { 
    title: 'Sua reserva vale prêmios! 💎', 
    desc: 'Pontue a cada 2 diárias e troque por prêmios exclusivos!', 
    icon: '�' 
  },
  { 
    title: 'Acomodações Amplas', 
    desc: 'Quartos projetados para conforto máximo — sinta-se em casa.', 
    icon: '🏨' 
  },
  { 
    title: 'Atendimento 24h', 
    desc: 'Equipe à disposição 24 horas, com serviço atencioso e eficiente.', 
    icon: '🔔' 
  },
]

const TopBar = () => (
  <div className="bg-[#081a2f] text-white/80 py-3 border-b border-white/10">
    <div className="max-w-6xl mx-auto px-4 flex flex-wrap items-center justify-between gap-4 text-sm">
      <div className="flex items-center gap-2">
        <span>📍</span>
        <span>Rua Enfermeiro Ricardo Sanches, 22 - Braga, Cabo Frio - RJ - 28908-040</span>
      </div>
      <div className="flex items-center gap-6">
        <a href="tel:+552226485900" className="flex items-center gap-2 hover:text-amber-300 transition-all">
          <span>📞</span>
          <span>(22) 2648-5900</span>
        </a>
        <a 
          href="https://www.instagram.com/hotelrealcf/" 
          target="_blank" 
          rel="noopener noreferrer"
          className="hover:text-amber-300 transition-all"
        >
          Instagram
        </a>
        <a 
          href="https://api.whatsapp.com/send/?phone=552226485900&text=Ol%C3%A1%21+Gostaria+de+informa%C3%A7%C3%B5es+sobre+hospedagem.&type=phone_number&app_absent=0" 
          target="_blank" 
          rel="noopener noreferrer"
          className="hover:text-amber-300 transition-all"
        >
          WhatsApp
        </a>
      </div>
    </div>
  </div>
)

const Header = () => (
  <header className="relative z-10">
    <div className="max-w-6xl mx-auto px-4 py-5 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <img
          src="/images/hotel real cabo frio PNG.png"
          alt="Hotel Real Cabo Frio"
          width="150"
          height="150"
          className="rounded-full bg-white/10 p-1"
        />
        <div>
          <h1 className="text-xl font-semibold text-white">Hotel Real Cabo Frio</h1>
          <p className="text-sm text-amber-300">Cabo Frio - RJ</p>
        </div>
      </div>
      <nav className="hidden md:flex items-center gap-6 text-sm text-white/80">
        <a href="#inicio" className="hover:text-white transition-all">Início</a>
        {/* <a href="#acomodacoes" className="hover:text-white transition-all">Acomodações</a> */}
        <a href="#hotel" className="hover:text-white transition-all">O Hotel</a>
        <Link href="/login" className="flex items-center gap-2 hover:text-white transition-all">
          <span className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-white/10">🔒</span>
          Área Restrita
        </Link>
      </nav>
    </div>
  </header>
)

const HeroSection = () => (
  <section className="grid lg:grid-cols-2 gap-10 items-center pt-12">
    <div>
      <h2 className="text-4xl md:text-5xl font-semibold text-white mt-3">
        Hotel Real Cabo Frio
      </h2>
      <p className="text-2xl text-amber-300 mt-4 font-light">
        Seu lar longe de casa
      </p>
      <p className="text-lg text-blue-100/80 mt-4 max-w-xl">
        Sua reserva vale prêmios! 💎 Pontue a cada 2 diárias e troque por prêmios exclusivos!
      </p>
      <div className="flex flex-wrap gap-4 mt-8">
        <Link
          href="/reservar"
          aria-label="Reservar agora"
          className="px-8 py-3 rounded-full bg-amber-300 text-[#0b1f38] font-semibold shadow-lg shadow-amber-400/30 transition-all hover:-translate-y-0.5 hover:shadow-amber-400/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-200"
        >
          🏨 Reservar
        </Link>
        <a
          href="https://api.whatsapp.com/send/?phone=552226485900&text=Ol%C3%A1%21+Gostaria+de+informa%C3%A7%C3%B5es+sobre+hospedagem.&type=phone_number&app_absent=0"
          target="_blank"
          rel="noopener noreferrer"
          aria-label="WhatsApp"
          className="px-8 py-3 rounded-full border border-white/30 text-white/90 font-semibold transition-all hover:bg-white/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
        >
          WhatsApp
        </a>
        <a
          href="tel:+552226485900"
          aria-label="Ligar"
          className="px-8 py-3 rounded-full border border-white/30 text-white/90 font-semibold transition-all hover:bg-white/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
        >
          Ligar
        </a>
      </div>
    </div>
    <div className="relative">
      <div className="relative h-[360px] md:h-[420px] rounded-3xl overflow-hidden border border-white/20 shadow-2xl">
        <img
          src="/images/suites/entrada.jpg"
          alt="Entrada do Hotel Real"
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-tr from-[#0b1f38]/80 via-transparent to-transparent" />
      </div>
    </div>
  </section>
)

const PrimaryActions = () => (
  <section className="mt-16">
    <div className="grid md:grid-cols-2 gap-8">
      <Link
        href="/reservar"
        aria-label="Fazer reserva"
        className="group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-300/70 rounded-3xl"
      >
        <div className="relative bg-white/95 text-[#0b1f38] rounded-3xl p-8 shadow-2xl transition-all duration-300 group-hover:-translate-y-1 group-hover:shadow-amber-400/30">
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-amber-200 via-amber-400 to-amber-200" />
          <div className="flex items-center gap-4">
            <span className="w-12 h-12 rounded-2xl bg-amber-100 text-2xl flex items-center justify-center">🏨</span>
            <div>
              <h3 className="text-2xl font-semibold">Fazer Reserva</h3>
              <p className="text-slate-600 mt-2">
                Escolha datas, suíte ideal e garanta sua estadia com poucos cliques.
              </p>
            </div>
          </div>
          <div className="mt-6 font-semibold text-amber-600 flex items-center gap-2">
            🏨 Reservar agora <span className="transition-transform group-hover:translate-x-1">→</span>
          </div>
        </div>
      </Link>
      <Link
        href="/consultar-pontos"
        aria-label="Consultar pontos"
        className="group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/40 rounded-3xl"
      >
        <div className="relative bg-white/10 text-white rounded-3xl p-8 border border-white/20 backdrop-blur transition-all duration-300 group-hover:-translate-y-1 group-hover:shadow-xl">
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-white/20 via-white/50 to-white/20" />
          <div className="flex items-center gap-4">
            <span className="w-12 h-12 rounded-2xl bg-white/15 text-2xl flex items-center justify-center">💎</span>
            <div>
              <h3 className="text-2xl font-semibold">Consultar Pontos</h3>
              <p className="text-blue-100/80 mt-2">
                Veja benefícios exclusivos e saldo de fidelidade com seu CPF.
              </p>
            </div>
          </div>
          <div className="mt-6 font-semibold text-white/90 flex items-center gap-2">
            💎 Consultar pontos <span className="transition-transform group-hover:translate-x-1">→</span>
          </div>
        </div>
      </Link>
    </div>
  </section>
)

// const SuitesSection = () => (
//   <section id="acomodacoes" className="mt-20">
//     <div className="text-center mb-10">
//       <h3 className="text-3xl md:text-4xl font-semibold text-white">Acomodações</h3>
//       <p className="text-blue-100/80 mt-3 max-w-2xl mx-auto">
//         Ver todas
//       </p>
//     </div>
//     <div className="grid lg:grid-cols-2 gap-8">
//       {suites.map((suite) => (
//         <div
//           key={suite.name}
//           className={`relative rounded-3xl overflow-hidden border ${
//             suite.featured
//               ? 'border-amber-300/80 bg-white/10 shadow-2xl'
//               : 'border-white/10 bg-white/5'
//           } backdrop-blur transition-all duration-300 hover:-translate-y-1 hover:shadow-xl`}
//         >
//           {suite.featured && (
//             <span className="absolute top-4 right-4 bg-amber-300 text-[#0b1f38] text-xs font-bold px-3 py-1 rounded-full z-10">
//               DESTAQUE
//             </span>
//           )}
//           <div className="relative h-64">
//             <img
//               src={suite.image}
//               alt={suite.name}
//               className="absolute inset-0 w-full h-full object-cover"
//             />
//           </div>
//           <div className="p-6 text-white">
//             <h4 className="text-xl font-semibold">{suite.name}</h4>
//             <p className="text-blue-100/80 mt-2 text-sm">{suite.description}</p>
//             <div className="flex flex-wrap gap-2 mt-4 text-xs text-white/80">
//               {suite.details.map((detail) => (
//                 <span key={detail} className="px-3 py-1 rounded-full bg-white/10">
//                   {detail}
//                 </span>
//               ))}
//             </div>
//             <div className="mt-6 flex gap-3">
//               <Link
//                 href="/reservar"
//                 aria-label={`Reservar ${suite.name}`}
//                 className="flex-1 px-4 py-2 rounded-full bg-amber-300 text-[#0b1f38] text-sm font-semibold text-center transition-all hover:bg-amber-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-200"
//               >
//                 Detalhes
//               </Link>
//               <a
//                 href="https://api.whatsapp.com/send/?phone=552226485900&text=Ol%C3%A1%21+Gostaria+de+informa%C3%A7%C3%B5es+sobre+hospedagem.&type=phone_number&app_absent=0"
//                 target="_blank"
//                 rel="noopener noreferrer"
//                 aria-label={`WhatsApp para ${suite.name}`}
//                 className="flex-1 px-4 py-2 rounded-full bg-white/10 text-white text-sm font-semibold text-center transition-all hover:bg-white/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
//               >
//                 WhatsApp
//               </a>
//             </div>
//           </div>
//         </div>
//       ))}
//     </div>
//   </section>
// )

const BenefitsSection = () => (
  <section id="hotel" className="mt-20">
    <div className="text-center mb-10">
      <h3 className="text-3xl md:text-4xl font-semibold text-white">Por que escolher o Hotel Real?</h3>
      <p className="text-blue-100/80 mt-3 max-w-2xl mx-auto">
        Sua reserva vale prêmios! 💎 Pontue a cada 2 diárias e troque por prêmios exclusivos!
      </p>
    </div>
    <div className="grid md:grid-cols-3 gap-6">
      {benefits.map((benefit) => (
        <div
          key={benefit.title}
          className="bg-white/10 border border-white/20 backdrop-blur rounded-2xl p-8 text-white text-center shadow-lg transition-all duration-300 hover:-translate-y-1 hover:bg-white/15"
        >
          <span className="text-5xl">{benefit.icon}</span>
          <h4 className="text-xl font-semibold mt-4">{benefit.title}</h4>
          <p className="text-blue-100/80 mt-2 text-sm">{benefit.desc}</p>
        </div>
      ))}
    </div>
    <div className="text-center mt-10">
      <Link
        href="/reservar"
        className="inline-block px-8 py-3 rounded-full bg-amber-300 text-[#0b1f38] font-semibold shadow-lg shadow-amber-400/30 transition-all hover:-translate-y-0.5 hover:shadow-amber-400/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-200"
      >
        Reservar agora
      </Link>
    </div>
  </section>
)

const LocationSection = () => (
  <section className="mt-20">
    <div className="text-center mb-10">
      <h3 className="text-3xl md:text-4xl font-semibold text-white">A 600 Metros da Praia</h3>
      <p className="text-blue-100/80 mt-3 max-w-2xl mx-auto">
        Estamos pertinho de tudo que importa em Cabo Frio. Veja no mapa!
      </p>
    </div>
    <div className="bg-white/10 border border-white/20 backdrop-blur rounded-3xl overflow-hidden shadow-2xl">
      <iframe
        src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3677.8!2d-42.0187!3d-22.8794!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x971850c8b8b8b8b8%3A0x1234567890!2sRua%20Enfermeiro%20Ricardo%20Sanches%2C%2022%20-%20Braga%2C%20Cabo%20Frio%20-%20RJ%2C%2028908-040!5e0!3m2!1spt-BR!2sbr!4v1234567890"
        width="100%"
        height="450"
        style={{ border: 0 }}
        allowFullScreen=""
        loading="lazy"
        referrerPolicy="no-referrer-when-downgrade"
        className="w-full"
      ></iframe>
    </div>
  </section>
)

const TestimonialsSection = () => (
  <section className="mt-20">
    <div className="text-center mb-10">
      <h3 className="text-3xl md:text-4xl font-semibold text-white">O que nossos hóspedes dizem</h3>
      <p className="text-blue-100/80 mt-3">A experiência de quem já se hospedou conosco.</p>
    </div>
    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
      {testimonials.map((testimonial) => (
        <div
          key={testimonial.name}
          className="bg-white/10 border border-white/15 rounded-2xl p-6 text-white/90 backdrop-blur transition-all duration-300 hover:-translate-y-1 hover:bg-white/15"
        >
          <p className="text-sm text-white/80 italic leading-relaxed">"{testimonial.quote}"</p>
          <p className="mt-4 font-semibold text-amber-300">— {testimonial.name}</p>
        </div>
      ))}
    </div>
  </section>
)

const Footer = () => (
  <footer className="bg-[#081a2f] text-white/80 py-12 mt-20 border-t border-white/10">
    <div className="max-w-6xl mx-auto px-4">
      <div className="grid md:grid-cols-5 gap-8">
        <div>
          <div className="flex items-center gap-3 mb-4">
            <img
              src="/images/hotel real cabo frio PNG.png"
              alt="Hotel Real Cabo Frio"
              width={48}
              height={48}
              className="rounded-full bg-white/10 p-1"
            />
            <div>
              <h3 className="text-xl font-semibold text-white">Hotel Real Cabo Frio</h3>
              <p className="text-amber-300 text-sm">Cabo Frio - RJ</p>
            </div>
          </div>
          <p className="text-sm text-white/70 mb-4">
            O melhor da hospitalidade na Região dos Lagos, com charme, conforto e atendimento premium.
          </p>
          <p className="text-xs text-white/50">CNPJ: 29.269.359/0001-40</p>
        </div>
        <div>
          <h4 className="font-semibold text-white mb-4">Endereço</h4>
          <p className="text-sm"> Rua Enfermeiro Ricardo Sanches, 22</p>
          <p className="text-sm">Braga, Cabo Frio - RJ</p>
          <p className="text-sm">28908-040</p>
        </div>
        <div>
          <h4 className="font-semibold text-white mb-4">Contato</h4>
          <p className="text-sm mb-3">(22) 2648-5900</p>
          <p className="text-sm mb-3">contato@hotelrealcabofrio.com.br</p>
          <div className="space-y-2">
            <a
              href="https://www.instagram.com/hotelrealcf/"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-sm hover:text-amber-300 transition-all"
            >
              Instagram: @hotelrealcf
            </a>
            <a
              href="https://api.whatsapp.com/send/?phone=552226485900&text=Ol%C3%A1%21+Gostaria+de+informa%C3%A7%C3%B5es+sobre+hospedagem.&type=phone_number&app_absent=0"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-sm hover:text-amber-300 transition-all"
            >
              WhatsApp: (22) 2648-5900
            </a>
          </div>
        </div>
        {/* <div>
          <h4 className="font-semibold text-white mb-4">Acomodações</h4>
          <div className="space-y-2 text-sm">
            <Link href="/reservar" className="block hover:text-amber-300 transition-all">→ Suíte Luxo</Link>
            <Link href="/reservar" className="block hover:text-amber-300 transition-all">→ Suíte Master</Link>
            <Link href="/reservar" className="block hover:text-amber-300 transition-all">→ Suíte Real</Link>
          </div>
        </div> */}
        <div>
          <h4 className="font-semibold text-white mb-4">O Hotel</h4>
          <div className="space-y-2 text-sm">
            <Link href="/reservar" className="block hover:text-amber-300 transition-all">→ Fazer Reserva</Link>
            <Link href="/consultar-pontos" className="block hover:text-amber-300 transition-all">→ Consultar Pontos</Link>
            <Link href="/login" className="block hover:text-amber-300 transition-all">→ Área Restrita</Link>
          </div>
        </div>
      </div>
      <div className="border-t border-white/10 mt-10 pt-6 text-center text-sm text-white/60">
        <p>© 2025 Hotel Real Cabo Frio — Todos os direitos reservados. Desenvolvido por André Kaique Dell Isola - Andryll Solutions.</p>
      </div>
    </div>
  </footer>
)

export default function Home() {
  return (
    <div className="min-h-screen text-white bg-[#0b1f38]">
      <TopBar />
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 -z-10">
          <img
            src="https://images.unsplash.com/photo-1501117716987-c8e1ecb2100b?auto=format&fit=crop&w=2000&q=80"
            alt="Hotel Real Cabo Frio"
            className="absolute inset-0 w-full h-full object-cover opacity-35"
          />
        </div>
        <div className="absolute inset-0 -z-10 bg-gradient-to-b from-[#0b1f38]/10 via-[#0b1f38] to-[#0b1f38]" />
        <Header />
        <main id="inicio" className="max-w-6xl mx-auto px-4 pb-20">
          <HeroSection />
          <PrimaryActions />
          {/* <SuitesSection /> */}
          <BenefitsSection />
          <TestimonialsSection />
          <LocationSection />
        </main>
      </div>
      <Footer />
    </div>
  )
}
