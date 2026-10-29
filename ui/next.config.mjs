/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  compress: false, // keep SSE proxy unbuffered
};
export default nextConfig;
