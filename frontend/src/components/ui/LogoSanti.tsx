'use client'

import React from 'react'
import Image from 'next/image'

interface LogoSantiProps {
  sizeClassName?: string // Permitir modularidad de tamaño (ej: "w-20 h-20" o "w-24 h-24")
}

export const LogoSanti: React.FC<LogoSantiProps> = ({ sizeClassName = "w-24 h-24" }) => {
  return (
    /* CONTENEDOR PADRE: Forza un recuadro cuadrado rígido con perspectiva y aislamiento de desbordamiento controlado */
    <div className={`relative ${sizeClassName} aspect-square flex items-center justify-center p-2 bg-transparent overflow-visible`}>
      <Image
        src="/brand/logo-santi.svg"
        alt="Isotipo Integral S.A.N.T.I."
        fill
        priority
        sizes="(max-width: 768px) 80px, 96px"
        className="object-contain select-none pointer-events-none filter drop-shadow-[0_4px_16px_rgba(13,148,136,0.35)] transition-transform duration-500 group-hover:scale-105"
      />
    </div>
  )
}
