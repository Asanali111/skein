import Hero from "@/components/Hero";
import Problem from "@/components/Problem";
import DogfoodCallout from "@/components/DogfoodCallout";
import Features from "@/components/Features";
import InstallBlock from "@/components/InstallBlock";
import Comparison from "@/components/Comparison";
import Footer from "@/components/Footer";

export default function Page() {
  return (
    <main>
      <Hero />
      <Problem />
      <DogfoodCallout />
      <Features />
      <InstallBlock />
      <Comparison />
      <Footer />
    </main>
  );
}
