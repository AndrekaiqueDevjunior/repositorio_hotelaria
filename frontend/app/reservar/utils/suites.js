export const getSuiteDescription = (tipo) => {
  const descriptions = {
    'LUXO': {
      titulo: 'Suíte Luxo',
      descricao: 'Conforto e elegância com vista privilegiada',
      amenidades: ['Ar condicionado', 'TV 32"', 'Frigobar', 'Wi-Fi', 'Varanda', 'Secador de cabelo']
    },
    'MASTER': {
      titulo: 'Suíte Master',
      descricao: 'Espaço amplo com acabamentos premium',
      amenidades: ['Ar condicionado Split', 'TV 50"', 'Frigobar completo', 'Wi-Fi', 'Varanda', 'Secador de cabelo']
    },
    'REAL': {
      titulo: 'Suíte Real',
      descricao: 'O máximo em luxo e exclusividade',
      amenidades: ['Ar condicionado Split', 'TV 55" Smart', 'Frigobar premium', 'Wi-Fi 5G', 'Terraço privativo', 'Banheira', 'Secador de cabelo']
    },
    'DUPLA': {
      titulo: 'Suíte Dupla',
      descricao: 'Espaço confortável para casais',
      amenidades: ['Ar condicionado', 'TV 42"', 'Frigobar', 'Wi-Fi', 'Varanda', 'Secador de cabelo']
    }
  }
  return descriptions[tipo] || { titulo: tipo, descricao: '', amenidades: [] }
}

export const getSuiteImage = (tipo) => {
  const images = {
    'REAL': '/images/suites/suite-real.png',
    'MASTER': '/images/suites/suite-master.png',
    'DUPLA': '/images/suites/suite-dupla.png',
    'LUXO': '/images/suites/suite-luxo.png'
  }
  return images[tipo] || '/images/suites/suite-luxo.png'
}
