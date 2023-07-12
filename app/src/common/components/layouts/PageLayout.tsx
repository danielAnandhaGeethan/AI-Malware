import React from "react";
import { Divider } from "@chakra-ui/react";
import { UserCircleIcon } from "@heroicons/react/24/outline";
import clsx from "clsx";
import { Component } from "../../types/component";
import { Link } from "../elements/Link";
import { pages } from "../../../utils/constants/page";

type Props = {
  title: string;
};

export const PageLayout: React.FC<Props & Component> = ({
  title,
  className,
  children,
}) => {
  return (
    <div className="body flex min-h-screen">
      <aside className="z-50 flex flex-col gap-4 flex-shrink-0 justify-between border-r-2">
        <div className="grid gap-4 py-4 ">
          <img className="w-18 h-15 mx-auto " src="/assets/image/small_logo.png" alt="MegVerse"/>

          <div className="grid gap-2">
            {pages.map(({ name, href, Icon }) => (
              <Link
                key={name}
                to={href}
                className="flex flex-col items-center gap-1"
                icon={<Icon className="w-8 h-8" />}
                isNavLink
              >
                <p className="font-semibold">{name}</p>
              </Link>
            ))}
          </div>
        </div>

        <Link
          to="/login"
          className="p-4 flex flex-col items-center gap-1"
          icon={<UserCircleIcon className="w-8 h-8" />}
        >
          <p className="font-semibold">Login</p>
        </Link>
      </aside>

      <section className="z-50 w-full p-4 flex flex-col gap-4">
        {title && <h1>{title}</h1>}

        <Divider className="-mt-1" />

        <div className={clsx("card", className)}>{children}</div>
      </section>
    </div>
  );
};
