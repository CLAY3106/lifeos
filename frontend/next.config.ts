import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  devIndicators: {
    position: "bottom-right",
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'https://lifeos-zggd.onrender.com/:path*',
      },
    ]
  },
};

export default nextConfig;